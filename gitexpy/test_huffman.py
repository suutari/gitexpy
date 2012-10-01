from . import huffman
from .randomstring import generate_random_string

def test():
    for string in (
        generate_random_string(),
        'hello_thee__this_is_test__z_is_symbol',
        'ab',
        'aabc',
        ):
        yield (check_with_string, string)

def check_with_string(string):
    (symbols, freqs)= huffman.count_symbol_frequencies(string)
    huffman_codemap = huffman.make_huffman_codemap(symbols, freqs)
    assert huffman.is_prefix_codemap(huffman_codemap)
    huffman.print_codemap(huffman_codemap)
    huffman_codemap = huffman.normalize_codemap(huffman_codemap)
    assert huffman.is_prefix_codemap(huffman_codemap)
    huffman.print_codemap(huffman_codemap)
    encoded = huffman.encode_with_codemap(string, huffman_codemap)
    decoded = huffman.decode_with_codemap(encoded, huffman_codemap)
    decoded_with_align = huffman.decode_with_codemap(
        encoded, huffman_codemap, align=True)
    assert decoded == string
    ent = huffman.entropy(freqs)
    lam = huffman.lambda_of_codemap(freqs, huffman_codemap)
    lam2 = len(encoded) / float(len(string))
    assert ent <= lam
    assert lam <= 1 + ent
    assert abs(lam - lam2) < 0.00001
    print(string)
    print(encoded)
    print(decoded_with_align)
    print('Entropy: %s bits/symbol' % ent)
    print('Lambda of the codemap: %s bits/symbol' % lam)

def test_deflate_mode2_code():
    deflate_mode2_code = {
        i: c
        for (i,c) in enumerate(
            huffman.normalized_huffman_code(
                144*[8] + 112*[9] + 24*[7] + 8*[8]))}
    assert huffman.is_prefix_codemap(deflate_mode2_code)
    assert huffman.is_normalized_codemap(deflate_mode2_code)
    assert deflate_mode2_code[000] == '00110000'
    assert deflate_mode2_code[143] == '10111111'
    assert deflate_mode2_code[144] == '110010000'
    assert deflate_mode2_code[255] == '111111111'
    assert deflate_mode2_code[256] == '0000000'
    assert deflate_mode2_code[279] == '0010111'
    assert deflate_mode2_code[280] == '11000000'
    assert deflate_mode2_code[287] == '11000111'
    print('test_deflate_mode2_code: OK')
