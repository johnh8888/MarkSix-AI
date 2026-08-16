# -*- coding: utf-8 -*-

from collections import Counter, defaultdict

import math


def row_numbers(row):

    return [
        row["n1"],
        row["n2"],
        row["n3"],
        row["n4"],
        row["n5"],
        row["n6"],
        row["special"],
    ]


def get_special(row):

    return int(row["special"])


def frequency_scores(rows):

    counter = Counter()

    for row in rows:

        for n in row_numbers(row):

            counter[n] += 1

    total = max(len(rows), 1)

    scores = {}

    for n in range(1, 50):

        scores[n] = counter[n] / (
            total * 7
        )

    return scores


def omission_scores(rows):

    result = {}

    for number in range(1, 50):

        omission = len(rows)

        for i, row in enumerate(rows):

            if number in row_numbers(row):

                omission = i
                break

        result[number] = omission

    return result


def special_frequency(rows):

    counter = Counter()

    for row in rows:

        counter[get_special(row)] += 1

    total = max(len(rows), 1)

    return {
        n: counter[n] / total
        for n in range(1, 50)
    }


def special_omission(rows):

    result = {}

    for number in range(1, 50):

        omission = len(rows)

        for i, row in enumerate(rows):

            if get_special(row) == number:

                omission = i
                break

        result[number] = omission

    return result


def size_value(number):

    # 01-24 小
    # 25-49 大
    return 0 if number <= 24 else 1


def parity_value(number):

    return 0 if number % 2 == 0 else 1


def number_basic_features(number):

    return {
        "number": number,

        "size": size_value(number),

        "parity": parity_value(number),

        "tail": number % 10,

        "zone": (
            1 if number <= 16
            else 2 if number <= 33
            else 3
        ),
    }


def size_stats(rows):

    big = 0
    small = 0

    for row in rows:

        n = get_special(row)

        if n >= 25:
            big += 1
        else:
            small += 1

    total = big + small

    if total == 0:
        return {
            "big": 0.5,
            "small": 0.5
        }

    return {
        "big": big / total,
        "small": small / total
    }


def parity_stats(rows):

    odd = 0
    even = 0

    for row in rows:

        n = get_special(row)

        if n % 2:
            odd += 1
        else:
            even += 1

    total = odd + even

    if total == 0:
        return {
            "odd": 0.5,
            "even": 0.5
        }

    return {
        "odd": odd / total,
        "even": even / total
    }


def build_number_features(rows):

    short_rows = rows[:30]
    medium_rows = rows[:100]
    long_rows = rows[:300]

    features = {}

    short_freq = special_frequency(short_rows)
    medium_freq = special_frequency(medium_rows)
    long_freq = special_frequency(long_rows)

    short_omission = special_omission(short_rows)

    for number in range(1, 50):

        features[number] = {
            "short_freq": short_freq[number],

            "medium_freq": medium_freq[number],

            "long_freq": long_freq[number],

            "omission": short_omission[number],

            **number_basic_features(number)
        }

    return features
