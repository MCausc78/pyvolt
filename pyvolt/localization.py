"""
The MIT License (MIT)

Copyright (c) 2024-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from .enums import Enum


class Language(Enum):
    english = 'en'
    english_simplified = 'en_US'

    arabic = 'ar'
    assamese = 'as'
    azerbaijani = 'az'
    belarusian = 'be'
    bulgarian = 'bg'
    bengali = 'bn'
    breton = 'br'
    catalonian = 'ca'
    cebuano = 'ceb'
    central_kurdish = 'ckb'
    czech = 'cs'
    danish = 'da'
    german = 'de'
    greek = 'el'
    spanish = 'es'
    spanish_latin_america = 'es_419'
    estonian = 'et'
    finnish = 'fi'
    filipino = 'fil'
    french = 'fr'
    irish = 'ga'
    hindi = 'hi'
    croatian = 'hr'
    hungarian = 'hu'
    armenian = 'hy'
    indonesian = 'id'
    icelandic = 'is'
    italian = 'it'
    japanese = 'ja'
    korean = 'ko'
    luxembourgish = 'lb'
    lithuanian = 'lt'
    macedonian = 'mk'
    malay = 'ms'
    norwegian_bokmal = 'nb_NO'
    dutch = 'nl'
    persian = 'fa'
    polish = 'pl'
    portuguese_brazil = 'pt_BR'
    portuguese_portugal = 'pt_PT'
    romanian = 'ro'
    russian = 'ru'
    slovak = 'sk'
    slovenian = 'sl'
    albanian = 'sq'
    serbian = 'sr'
    sinhalese = 'si'
    swedish = 'sv'
    tamil = 'ta'
    thai = 'th'
    turkish = 'tr'
    ukranian = 'uk'
    urdu = 'ur'
    venetian = 'vec'
    vietnamese = 'vi'
    chinese_simplified = 'zh_Hans'
    chinese_traditional = 'zh_Hant'
    latvian = 'lv'

    tokipona = 'tokipona'
    esperanto = 'esperanto'

    owo = 'owo'
    pirate = 'pr'
    bottom = 'bottom'
    leet = 'leet'
    piglatin = 'piglatin'
    enchantment_table = 'enchantment'


__all__ = ('Language',)
