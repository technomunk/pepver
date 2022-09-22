# pepver


PEP-440 version parsing, interpretation and manipulation.


```py
from pepver import Version


version = Version.parse("0!1.2.3.4a5.post6.dev7+8.9")
version.epoch  # 0
version.release  # 1, 2, 3, 4
version.major  # 1
version.minor  # 2
version.micro  # 3
version.pre  # a 5
version.post  # 6
version.dev  # 7
version.local  # "8.9"


normalized = Version.parse("00!1.a-5-11dev.1")
str(normalized)  # 0!1a5.post11.dev1
```
