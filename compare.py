#! /usr/bin/env python3

from hypothesis import given, settings
import hypothesis.strategies as st

def encode_field(field):
    b = b''
    if isinstance(field, str):
        b += b'\x00'
        utf_encoded = field.encode('utf8')
        b+= utf_encoded.replace(b'\x00', b'\x00ff')
    elif isinstance(field, int):
        b += b'\x00'
        b += field.to_bytes(8, 'big')
    else:
        raise Exception('unsupported field type {}'.format(type(field)))
    return b


comma = b'\x00'


def array_to_bytes(arr):
    b = b''
    for field in arr:
        b += encode_field(field)
        b += comma
    return b


test_data = [
    [[1, 2, 3], [1, 2, 3]],
    [["this is a really long string"], ["short"]],
    [["this is a really long string", 2, 3], ["short", 2, 3]],
    [[2 ** 16], [2 ** 15]],
    [[1, 0, 1, "prerelease-101"], [1, 0, 1, "prerelease-1000"]],
    # this one below is one of the trickier examples
    [["abc"], ["a", "b", "c"]],
]

positive_integer = st.integers(0, (2 ** 64)-1)

text = st.text(min_size=0, max_size=128)

three_part_tuple = st.tuples(positive_integer, positive_integer, text)
two_part_tuple = st.tuples(text, positive_integer)

@st.composite
def pair_of_version_list_with_same_types(draw):
    generators = [positive_integer, text]
    length = draw(st.integers(min_value=1, max_value=8))
    chosen_indices = draw(st.lists(st.integers(min_value=0, max_value=len(generators)-1), min_size=length, max_size=length))
    chosen_indices_to_generators = [generators[i] for i in chosen_indices]

    a = draw(st.tuples(*chosen_indices_to_generators))

    length_b = draw(st.integers(min_value=1, max_value=length))
    b = draw(st.tuples(*chosen_indices_to_generators[:length_b]))
    return (a, b)


@settings(max_examples=1000000)
@given(pair_of_version_list_with_same_types())
def test_compare(args):
    a, b = args
    control = a < b
    candidate = array_to_bytes(a) < array_to_bytes(b)
    assert control == candidate


if __name__ == '__main__':
    test_compare()
    for (a, b) in test_data:
        control = a < b
        candidate = array_to_bytes(a) < array_to_bytes(b)
        if not control == candidate:
            print('Failure!')
            print(f'Control={control}')
            print(f'Candidate={candidate}')
            print(a)
            print(b)
            print(array_to_bytes(a))
            print(array_to_bytes(b))
