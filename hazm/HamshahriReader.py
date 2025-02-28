"""این ماژول شامل کلاس‌ها و توابعی برای خواندن پیکرهٔ همشهری است.

[پیکرهٔ
همشهری](https://www.peykaregan.ir/dataset/%D9%85%D8%AC%D9%85%D9%88%D8%B9%D9%87-
%D9%87%D9%85%D8%B4%D9%87%D8%B1%DB%8C) حاوی
۳۱۸ هزار خبر از روزنامه همشهری از سال‌های ۱۳۷۵ تا ۱۳۸۶ است. این داده‌ها با
crawl
کردن وب‌سایت همشهری و گذر از چندمرحله پیش‌پردازش و برچسب‌زنی تهیه شده است. همهٔ
این خبرها دارای برچسب CAT بوده و رده‌بندی موضوعی آن مشخص است. این پیکره توسط
گروه تحقیقاتی پایکاه دادهٔ دانشگاه تهران و با حمایت مرکز تحقیقات مخابرات ایران
تهیه شده است.

"""


import os
import re
import sys
from typing import Iterator
from xml.dom import minidom


class HamshahriReader:
    """این کلاس شامل توابعی برای خواندن پیکرهٔ همشهری است.

    Args:
        root: مسیر فولدرِ حاوی فایل‌های پیکرهٔ همشهری.

    """

    def __init__(self, root: str):
        self._root = root
        self._invalids = {
            "hamshahri.dtd",
            "HAM2-960622.xml",
            "HAM2-960630.xml",
            "HAM2-960701.xml",
            "HAM2-960709.xml",
            "HAM2-960710.xml",
            "HAM2-960711.xml",
            "HAM2-960817.xml",
            "HAM2-960818.xml",
            "HAM2-960819.xml",
            "HAM2-960820.xml",
            "HAM2-961019.xml",
            "HAM2-961112.xml",
            "HAM2-961113.xml",
            "HAM2-961114.xml",
            "HAM2-970414.xml",
            "HAM2-970415.xml",
            "HAM2-970612.xml",
            "HAM2-970614.xml",
            "HAM2-970710.xml",
            "HAM2-970712.xml",
            "HAM2-970713.xml",
            "HAM2-970717.xml",
            "HAM2-970719.xml",
            "HAM2-980317.xml",
            "HAM2-040820.xml",
            "HAM2-040824.xml",
            "HAM2-040825.xml",
            "HAM2-040901.xml",
            "HAM2-040917.xml",
            "HAM2-040918.xml",
            "HAM2-040920.xml",
            "HAM2-041025.xml",
            "HAM2-041026.xml",
            "HAM2-041027.xml",
            "HAM2-041230.xml",
            "HAM2-041231.xml",
            "HAM2-050101.xml",
            "HAM2-050102.xml",
            "HAM2-050223.xml",
            "HAM2-050224.xml",
            "HAM2-050406.xml",
            "HAM2-050407.xml",
            "HAM2-050416.xml",
        }
        self._paragraph_pattern = re.compile(r"(\n.{0,50})(?=\n)")

    def docs(self) -> Iterator[dict[str, str]]:
        """خبرها را برمی‌گرداند.

        هر خبر، شی‌ای متشکل از این پارامتر است:

        - شناسه (`id`)
        - عنوان (`title`)
        - متن (`text`)
        - شماره (`issue`)
        - موضوعات (`categories`)

        Examples:
            >>> hamshahri = HamshahriReader(root='corpora/hamshahri')
            >>> next(hamshahri.docs())['id']
            'HAM2-750403-001'

        Yields:
            خبر بعدی.

        """

        for root, dirs, files in os.walk(self._root):
            for name in sorted(files):
                if name in self._invalids:
                    continue

                try:
                    elements = minidom.parse(os.path.join(root, name))
                    for element in elements.getElementsByTagName("DOC"):
                        doc = {
                            "id": (
                                element.getElementsByTagName("DOCID")[0]
                                .childNodes[0]
                                .data
                            ),
                            "issue": (
                                element.getElementsByTagName("ISSUE")[0]
                                .childNodes[0]
                                .data
                            ),
                        }

                        for cat in element.getElementsByTagName("CAT"):
                            doc[
                                "categories_" + cat.attributes["xml:lang"].value
                            ] = cat.childNodes[0].data.split(".")

                        for date in element.getElementsByTagName("DATE"):
                            if date.attributes["calender"].value == "Persian":
                                doc["date"] = date.childNodes[0].data

                        elm = element.getElementsByTagName("TITLE")[0]
                        doc["title"] = (
                            elm.childNodes[1].data if len(elm.childNodes) > 1 else ""
                        )

                        doc["text"] = ""
                        for item in element.getElementsByTagName("TEXT")[0].childNodes:
                            if item.nodeType == 4:  # CDATA
                                doc["text"] += item.data

                        # refine text
                        doc["text"] = self._paragraph_pattern.sub(
                            r"\1\n", doc["text"]
                        ).replace("\no ", "\n")

                        yield doc

                except Exception as e:
                    print("error in reading", name, e, file=sys.stderr)

    def texts(self) -> Iterator[str]:
        """فقط متن خبرها را در قالب یک برمی‌گرداند.

        این تابع صرفاً برای راحتی بیشتر تهیه شده وگرنه با تابع
        ‍[docs()][hazm.HamshahriReader.HamshahriReader.docs] و دریافت مقدار
        پراپرتی `text` نیز می‌توانید همین کار را انجام دهید.

        Yields:
            متنِ خبر بعدی.

        """
        for doc in self.docs():
            yield doc["text"]
