from rply import LexerGenerator, ParserGenerator

def parse_markdown(program):
    lg = LexerGenerator()
    lg.add('HEADING', r'\#{1,6}')
    lg.add('BOLD', r'\*\*|\_\_')
    lg.add('ITALIC', r'\*|\_')
    lg.add('STRIKETHROUGH', r'\~\~')
    lg.add('INLINE_CODE', r'\`')
    lg.add('CODE_BLOCK', r'\`\`\`')
    lg.add('LINK_OPEN', r'\[')
    lg.add('LINK_CLOSE', r'\]')
    lg.add('IMAGE', r'\!\[')
    lg.add('URL', r'\([^\)]+\)')
    lg.add('LIST_BULLET', r'\*|\+|\-')
    lg.add('LIST_NUMBER', r'\d+\.')
    lg.add('BLOCKQUOTE', r'\>')
    lg.add('NEWLINE', r'\n')
    lg.add('WHITESPACE', r'[ \t]+')
    lg.add('TEXT', r'[^#\*\n\[\]`!\-]+')

    lg.ignore(r'[ \t]+')

    lexer = lg.build()

    tokens_iter = lexer.lex(program)

    possible_tokens = [rule.name for rule in lexer.rules]

    pg = ParserGenerator(possible_tokens,
                           precedence=[
                               ('left', ['BOLD', 'ITALIC']),
                               ('left', ['LINK_OPEN', 'LINK_CLOSE', 'IMAGE', 'URL']),
                               ('left', ['INLINE_CODE', 'CODE_BLOCK']),
                               ('left', ['BLOCKQUOTE', 'LIST_BULLET', 'LIST_NUMBER']),
                               ('left', ['NEWLINE', 'WHITESPACE']),
                            ]
                        )
