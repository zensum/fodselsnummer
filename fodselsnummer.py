"""Functions for validation and generation of Norwegian fodselsnumbers"""

import re
from datetime import date, datetime, timedelta as td
from typing import Callable, Optional

FNR_REGEX = re.compile(r'\d{11}')


class FodselsnummerException(Exception):
    pass


class InvalidControlDigitException(FodselsnummerException):
    pass


def check_fnr(fnr: str, d_numbers=True, h_numbers=False, logger: Callable = lambda _x: None) -> bool:
    """
    Check if a number is a valid fodselsnumber.
    Args:
        fnr: A string containing the fodselsnummer to check
        d_numbers: True (the default) if d-numbers should be accepted
    Returns:
        True if it is a valid fodselsnummer, False otherwise.
    """
    if not FNR_REGEX.match(fnr):
        return False

    individual_number = int(fnr[6:9])
    day, month, year = int(fnr[0:2]), int(fnr[2:4]), int(fnr[4:6])
    if 41 <= day <= 71:  # if D-number
        if not d_numbers:
            logger('Day out of range in fnr')
            return False
        day -= 40

    if not (1 <= day <= 31):
        logger('Day out of range in fnr')
        return False
    if 41 <= month <= 52:  # if H-number
        if h_numbers:
            month -= 40
        else:
            logger('Month out of range')
            return False
    if not 1 <= month <= 12:
        logger('Month out of range in fnr')
        return False
    if individual_number <= 499:  # individual numbers 000-499 indicate person is born in 19XX
        year += 1900
    else:
        year += 2000
    if individual_number >= 900 and year >= 2040:
        year -= 100
    dob: Optional[date] = None
    try:
        dob = date(year=year, month=month, day=day)
    except ValueError:
        logger(f'{year}-{month}-{day} is not a valid date')
        return False

    try:
        generatedfnr = _generate_control_digits(fnr[0:9])
        logger('Control digit does not match fnr')
    except InvalidControlDigitException:
        return False

    if dob and dob > datetime.utcnow().date():
        logger('Date of fnr is larger than current date')
        return False

    if not bool(fnr == generatedfnr):
        logger('Control digit does not match fnr')
        return False
    return True


def generate_fnr_for_year(year, d_numbers):
    """
    Generates all the possible fodselsnumbers for a year.

    Args:
        year: The year to generate fodselsnummers for (integer)
        d_numbers: True if you want d-numbers as well, False otherwise.
    Returns:
        A list with all the possible fodselsnummers for that year.
    """
    allfnrs = []
    startdate = date(year, 1, 1)
    enddate = date(year, 12, 31)
    delta = enddate - startdate
    for i in range(delta.days + 1):
        allfnrs += generate_fnr_for_day(startdate + td(days=i), d_numbers)
    return allfnrs


def generate_fnr_for_day(day, d_numbers):
    """
    Generates all the possible fodselsnumbers for a day.

    Args:
        day: The day to generate fodslesnummers for (datetime)
        d_numbers: True if you want d-numbers as well, False otherwise.
    Returns:
        A list with all the possible fodselsnummers for that day.
    """
    thisdaysfnr = []
    stupid1900s = False
    datestring = day.strftime('%d%m%y')
    if d_numbers:
        dnrdatestring = str(int(datestring[0]) + 4) + datestring[1:]
    # ref:
    # http://www.kith.no/upload/5588/KITH1001-2010_Identifikatorer-for-personer_v1.pdf
    # Does not account for the 1800s, since this is for living persons
    # (this means that the 1800s list will be a little longer than necessary)
    if 1900 <= day.year <= 1999:
        individualmin = 000
        individualmax = 499
        if 1940 <= day.year <= 1999:
            stupid1900s = True
    else:
        individualmin = 500
        individualmax = 999
    for x in range(individualmin, individualmax + 1):
        individualnr = str(x).zfill(3)
        try:
            thisdaysfnr.append(_generate_control_digits(datestring + individualnr))
        except InvalidControlDigitException:
            pass
        if d_numbers:
            try:
                thisdaysfnr.append(_generate_control_digits(dnrdatestring + individualnr))
            except InvalidControlDigitException:
                pass
    # Bonus round because of the stupid 1900s
    if stupid1900s:
        for x in range(900, 1000):
            individualnr = str(x).zfill(3)
            try:
                thisdaysfnr.append(_generate_control_digits(datestring + individualnr))
            except InvalidControlDigitException:
                pass
            if d_numbers:
                try:
                    thisdaysfnr.append(_generate_control_digits(dnrdatestring + individualnr))
                except InvalidControlDigitException:
                    pass
    return thisdaysfnr


def _generate_control_digits(numbersofar):
    """Generates the magic control digits in a fodselsnumber"""
    staticnumbers1 = [3, 7, 6, 1, 8, 9, 4, 5, 2, 1]
    staticnumbers2 = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 1]
    sum1 = 0
    for x in range(0, 9):
        sum1 += int(numbersofar[x]) * staticnumbers1[x]
    rest = sum1 % 11
    if rest == 0:
        control1 = 0
    else:
        if 11 - rest != 10:
            control1 = 11 - rest
        else:
            raise InvalidControlDigitException
    numbersofar += str(control1)
    sum2 = 0
    for x in range(0, 10):
        sum2 += int(numbersofar[x]) * staticnumbers2[x]
    rest = sum2 % 11
    if rest == 0:
        control2 = 0
    else:
        if 11 - rest != 10:
            control2 = 11 - rest
        else:
            raise InvalidControlDigitException
    numbersofar += str(control2)
    return numbersofar
