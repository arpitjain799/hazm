"""این ماژول شامل کلاس‌ها و توابعی برای شناساییِ وابستگی‌های دستوری متن است.

"""


import os
import tempfile

from nltk.parse import DependencyGraph
from nltk.parse.api import ParserI
from nltk.parse.malt import MaltParser


class MaltParser(MaltParser):
    """این کلاس شامل توابعی برای شناسایی وابستگی‌های دستوری است.

    Args:
        tagger: نام تابع `POS Tagger`.
        lemmatizer: نام کلاس ریشه‌یاب.
        working_dir: محل ذخیره‌سازی `maltparser‍`.
        model_file: آدرس مدلِ از پیش آموزش دیده با پسوند `mco`.

    """

    def __init__(
        self,
        tagger: str,
        lemmatizer: str,
        working_dir: str = "resources",
        model_file: str = "langModel.mco",
    ):
        self.tagger = tagger
        self.working_dir = working_dir
        self.mco = model_file
        self._malt_bin = os.path.join(working_dir, "malt.jar")
        self.lemmatize = lemmatizer.lemmatize if lemmatizer else lambda w, t: "_"

    def parse_sents(self, sentences: str, verbose: bool = False) -> str:
        """گراف وابستگی را برمی‌گرداند.

        Args:
            sentences: جملاتی که باید گراف وابستگی آن‌ها استخراج شود.
            verbose: اگر `True` باشد وابستگی‌های بیشتری را برمی‌گرداند.

        Returns:
            گراف وابستگی.

        """
        tagged_sentences = self.tagger.tag_sents(sentences)
        return self.parse_tagged_sents(tagged_sentences, verbose)

    def parse_tagged_sents(self, sentences: list[list[tuple[str,str]]], verbose: bool = False) -> str:
        """گراف وابستگی‌ها را برای جملات ورودی برمی‌گرداند.

        Args:
            sentences: جملاتی که باید گراف وابستگی‌های آن استخراج شود.
            verbose: اگر `True` باشد وابستگی‌های بیشتری را برمی‌گرداند..

        Returns:
            گراف وابستگی جملات.

        Raises:
            Exception: در صورت بروز خطا یک اکسپشن عمومی صادر می‌شود.

        """
        input_file = tempfile.NamedTemporaryFile(
            prefix="malt_input.conll", dir=self.working_dir, delete=False
        )
        output_file = tempfile.NamedTemporaryFile(
            prefix="malt_output.conll", dir=self.working_dir, delete=False
        )

        try:
            for sentence in sentences:
                for i, (word, tag) in enumerate(sentence, start=1):
                    word = word.strip()
                    if not word:
                        word = "_"
                    input_file.write(
                        (
                            "\t".join(
                                [
                                    str(i),
                                    word.replace(" ", "_"),
                                    self.lemmatize(word, tag).replace(" ", "_"),
                                    tag,
                                    tag,
                                    "_",
                                    "0",
                                    "ROOT",
                                    "_",
                                    "_",
                                    "\n",
                                ]
                            )
                        ).encode("utf8")
                    )
                input_file.write(b"\n\n")
            input_file.close()

            cmd = [
                "java",
                "-jar",
                self._malt_bin,
                "-w",
                self.working_dir,
                "-c",
                self.mco,
                "-i",
                input_file.name,
                "-o",
                output_file.name,
                "-m",
                "parse",
            ]
            if self._execute(cmd, verbose) != 0:
                raise Exception("MaltParser parsing failed: %s" % (" ".join(cmd)))

            return (
                DependencyGraph(item)
                for item in open(output_file.name, encoding="utf8").read().split("\n\n")
                if item.strip()
            )

        finally:
            input_file.close()
            os.remove(input_file.name)
            output_file.close()
            os.remove(output_file.name)


class TurboParser(ParserI):
    """
    interfaces [TurboParser](http://www.ark.cs.cmu.edu/TurboParser/) which you must
    manually install

    """

    def __init__(self, tagger, lemmatizer: str, model_file: str):
        self.tagger = tagger
        self.lemmatize = lemmatizer.lemmatize if lemmatizer else lambda w, t: "_"

        import turboparser

        self._pturboparser = turboparser.PTurboParser()
        self.interface = self._pturboparser.create_parser()
        self.interface.load_parser_model(model_file)

    def parse_sents(self, sentences: list[list[tuple[str,str]]]) -> type[DependencyGraph]:
        tagged_sentences = self.tagger.tag_sents(sentences)
        return self.tagged_parse_sents(tagged_sentences)

    def tagged_parse_sents(self, sentences: list[list[tuple[str,str]]]) -> type[DependencyGraph]:
        input_file = tempfile.NamedTemporaryFile(
            prefix="turbo_input.conll", dir="resources", delete=False
        )
        output_file = tempfile.NamedTemporaryFile(
            prefix="turbo_output.conll", dir="resources", delete=False
        )

        try:
            for sentence in sentences:
                for i, (word, tag) in enumerate(sentence, start=1):
                    word = word.strip()
                    if not word:
                        word = "_"
                    input_file.write(
                        (
                            "\t".join(
                                [
                                    str(i),
                                    word.replace(" ", "_"),
                                    self.lemmatize(word, tag).replace(" ", "_"),
                                    tag,
                                    tag,
                                    "_",
                                    "0",
                                    "ROOT",
                                    "_",
                                    "_",
                                    "\n",
                                ]
                            )
                        ).encode("utf8")
                    )
                input_file.write(b"\n")
            input_file.close()

            self.interface.parse(input_file.name, output_file.name)

            return (
                DependencyGraph(item, cell_extractor=lambda cells: cells[1:8])
                for item in open(output_file.name, encoding="utf8").read().split("\n\n")
                if item.strip()
            )

        finally:
            input_file.close()
            os.remove(input_file.name)
            output_file.close()
            os.remove(output_file.name)


class DependencyParser(MaltParser):
    """این کلاس شامل توابعی برای شناسایی وابستگی‌های دستوری است.

    این کلاس تمام توابع خود را از کلاس
    [MaltParser][hazm.DependencyParser.MaltParser] به ارث می‌برد.

    Examples:
        >>> from hazm import POSTagger, Lemmatizer
        >>> parser = DependencyParser(tagger=POSTagger(model='resources/postagger.model'), lemmatizer=Lemmatizer())
        >>> parser.parse(['من', 'به', 'مدرسه', 'رفته بودم', '.']).tree().pprint()
        (رفته_بودم من (به مدرسه) .)

    """
