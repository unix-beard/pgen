pgen
====

Pattern Generator

######Short description######
Sometimes I need to generate sample data that follows a particular pattern (e.g., numbers consisting of these many digits (bin, dec, hex) or sequence of characters that look like a word, or a sequence of words that look like a sentence, or csv data)

For example, this pattern will generate a decimal number of 6 digits

    $ pgen.py -p "{d}{6}"
    687035

And this pattern will generate a string that looks like an md5 hash

    $ pgen.py -p "{x}{32}"
    2a313087a6ee8a0aee00806fb4b9f0b8
    
Whereas this pattern will generate 3 strings that look like sha-1 hashes

    $ pgen.py -c 3 -p "{x}{40}"
    dbd991ecff76bf37c38d71424556f8655b9be9c0
    a5f3f6da2cbee4b0d83310e428dc432220e6a879
    9e4ac36ddeb0fbc7fa8544a91eeb9ed05e8345c7
    
You get the idea

To produce binary looking data, you can use this pattern:

    $ pgen.py -c 4 -p "{{{{'0'}{'1'}}{@}}{8}{' '}}{4}"
    01101100 10100001 10101100 11110011
    00011011 00011111 10111000 11111010
    11100110 10111010 01111111 00100010
    01011100 01100001 00011010 11100011
    
Here ```@``` (at-sign) stands for 'any'. So, the pattern ```{{'0'}{'1'}}{@}``` will mean: please, generate me either '0' or '1' - I don't really care which one

And the pattern ```{{{'0'}{'1'}}{@}}{8}``` will generate 8 repitions of whatever is enclosed between ```{}``` preceding the quantifier (btw, ```{8}``` is a quantifier in this example)
So, we already have a pattern to generate 8-bit words. Let's separate them with space character and repeat each 8-bit word 4 times (i.e., we'll use ```{4}``` quantifier)

    {{{{'0'}{'1'}}{@}}{8}{' '}}{4}
    
Sometimes I need a piece of hex-looking text. Like this:

    2c ce 29 c5 92 75 84 04 44 75 28 fb fa f0 8d b5
    f8 cb 76 98 d4 04 2d 4e 61 d3 89 e0 80 93 40 bc
    76 29 79 a0 fc 86 ca 21 6b 8f 9d bd 09 f7 66 c0
    24 af 4e 73 f0 34 97 5c 1d 93 34 18 3a d9 d2 cb
    c2 c5 7c 9c a8 a0 2b 74 02 8a 24 65 97 8f 1c 5a
    bf 2f 43 8b 93 d6 75 0e 80 0b a4 04 bb c4 5b 91
    42 96 b1 52 41 7a d4 d8 35 b0 c3 bf 62 bc ab ef
    29 0b 42 00 b3 69 32 92 d0 d6 ea 87 ee 7b 76 a6
    
And with this simple pattern we can achieve just that:

    $ pgen.py -c 8 -p "{{x}{2}{' '}}{16}"
    
But I also need from time time a HEX-looking text (whith capital letters 'A' - 'F'):

    60 5B 09 71 C7 5A 75 1B D1 1C 06 2E B1 3F C6 6D
    E5 3C D0 FC 50 A1 BC 48 88 37 64 07 9D AA 8C F9
    33 6F 97 27 5B 75 17 D2 FB 39 59 E3 23 1C 5C D9
    59 BD 25 8F 78 A9 66 83 D4 D4 6E F3 59 07 6B C6
    D0 B1 BF BA 9D 02 29 FF 82 23 D0 20 B0 AD 6D 94
    8D 3E 41 88 AB CD 7F 31 B2 C3 43 6C 92 29 8B 34
    CE E6 A5 56 F8 3A FD 82 AA C5 A7 62 89 E3 19 9A
    27 B1 BF CF B6 61 0C 0F FE AD 82 18 F3 70 85 FB
    
To achieve that, let's use ```{X}``` built-in pattern:

    $ pgen.py -c 8 -p "{{X}{2}{' '}}{16}"

To play with arithmetic expressions, you can use this pattern:

    $ pgen.py -c 4 -p "{d}{1:2}{{{' + '}{' - '}{' * '}{' / '}}{@}{d}{1:2}}{2:4}"
    66 - 5 * 59
    8 - 8 - 5
    35 / 9 - 18 / 8
    3 / 60 / 3
