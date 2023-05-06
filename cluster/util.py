import re
from functools import lru_cache
from pathlib import Path
from typing import cast, Iterable, Optional, Union, Sized, TypeVar, Callable, Any
import pickle

import backoff
import numpy as np
import openai
import tiktoken
from tqdm import tqdm

DATA_DIR = Path(__file__).parent.parent / "data"
COMMENTS_PATH = DATA_DIR / "comments.csv"
COMMENT_EMBEDDINGS_PATH = DATA_DIR / "comments_embeddings.npz"
CLUSTERS_PATH = DATA_DIR / "clusters.p"

OPENAI_API_KEY_PATH = Path("~/.openai-api-key").expanduser()
CHAT_COMPLETE_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
ENCODING_NAME = "gpt2"  # encoding for text-davinci-003
ENCODING = tiktoken.get_encoding(ENCODING_NAME)
BACKOFF_RETRY_EXCEPTIONS = (ConnectionError,
                            openai.error.RateLimitError,
                            openai.error.Timeout,
                            openai.error.APIConnectionError)
BACKOFF_MAX_RETRIES = 4

T = TypeVar('T')

URL_REGEX = re.compile('''
(							# Capture 1: entire matched URL
  (?:
    https?:				# URL protocol and colon
    (?:
      /{1,3}						# 1-3 slashes
      |								#   or
      [a-z0-9%]						# Single letter or digit or '%'
      								# (Trying not to match e.g. "URI::Escape")
    )
    |							#   or
    							# looks like domain name followed by a slash:
    [a-z0-9.\-]+[.]
    (?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj| Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)
    /
  )
  (?:							# One or more:
    [^\s()<>{}\[\]]+						# Run of non-space, non-()<>{}[]
    |								#   or
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\)  # balanced parens, one level deep: (…(…)…)
    |
    \([^\s]+?\)							# balanced parens, non-recursive: (…)
  )+
  (?:							# End with:
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\)  # balanced parens, one level deep: (…(…)…)
    |
    \([^\s]+?\)							# balanced parens, non-recursive: (…)
    |									#   or
    [^\s`!()\[\]{};:'".,<>?«»“”‘’]		# not a space or one of these punct chars
  )
  |					# OR, the following to match naked domains:
  (?:
  	(?<!@)			# not preceded by a @, avoid matching foo@_gmail.com_
    [a-z0-9]+
    (?:[.\-][a-z0-9]+)*
    [.]
    (?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj| Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)
    \b
    /?
    (?!@)			# not succeeded by a @, avoid matching "foo.na" in "foo.na@example.com"
  )
)
''', re.VERBOSE | re.IGNORECASE)


def len_optional(xs: Union[Iterable, Sized]) -> Optional[int]:
    try:
        return len(xs)
    except TypeError:
        return None


def iter_with_progress(xs: Iterable[T], *, desc: Optional[str] = None, total: Optional[int] = None,
                       show_items: bool = False) -> Iterable[T]:
    if total is None:
        total = len_optional(xs)
    with tqdm(iterable=xs, desc=desc, total=total) as t:
        if not show_items:
            yield from t
        else:
            prefix = '' if desc is None else ' ' + desc
            for x in t:
                t.set_description(prefix + str(x))
                yield x


def save_using_tmp(filename: Union[str, Path], save_func: Callable[[Union[str, Path]], Any]):
    if not isinstance(filename, Path):
        filename = Path(filename)
    filename = cast(Path, filename)
    tmp_path = filename.with_stem(filename.stem + '-tmp')
    save_func(tmp_path)
    tmp_path.rename(filename)


def save_pickle_using_tmp(filename: Union[str, Path], obj: Any):
    def write(tmp_path: Path):
        with tmp_path.open('wb') as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

    save_using_tmp(filename, write)


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def count_words(t: str) -> int:
    return len(t.split())


def set_openai_key():
    if openai.api_key:  # if already set, possibly from env var, then do not change
        return
    openai.api_key = open(OPENAI_API_KEY_PATH).read().strip()


@lru_cache(maxsize=2_000)
@backoff.on_exception(backoff.expo, BACKOFF_RETRY_EXCEPTIONS, max_tries=BACKOFF_MAX_RETRIES)
def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> np.ndarray:
    result = openai.Embedding.create(
        model=model,
        input=text
    )
    return np.array(result["data"][0]["embedding"])


@backoff.on_exception(backoff.expo, BACKOFF_RETRY_EXCEPTIONS, max_tries=BACKOFF_MAX_RETRIES)
def chat_complete_stream(query: str, model: str, system_content: str = "You are a helpful assistant.", **kwds) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
        ],
        stream=True,
        **kwds
    )

    parts = []
    for chunk in response:
        c = chunk['choices'][0]['delta'].get('content')
        if c is not None:
            print(c, end='')
            parts.append(c)
    print()
    return ''.join(parts)
