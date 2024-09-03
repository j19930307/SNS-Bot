from dataclasses import dataclass
from typing import List


@dataclass
class Artist:
    ARTISTID: str
    ARTISTNAME: str

@dataclass
class Genre:
    GENRECODE: str
    GENRENAME: str

@dataclass
class Song:
    SONGID: str
    SONGNAME: str
    ALBUMID: str
    ALBUMNAME: str
    ARTISTLIST: List[Artist]
    PLAYTIME: str
    GENRELIST: List[Genre]
    CURRANK: str
    PASTRANK: str
    RANKGAP: str
    RANKTYPE: str
    ISMV: bool
    ISADULT: bool
    ISFREE: bool
    ISHITSONG: bool
    ISHOLDBACK: bool
    ISTITLESONG: bool
    ISSERVICE: bool
    ISTRACKZERO: bool
    ALBUMIMG: str
    ALBUMIMGPATH: str
    ALBUMIMGLARGE: str
    ALBUMIMGSMALL: str
    ISSUEDATE: str
    CTYPE: str
    CONTSTYPECODE: str