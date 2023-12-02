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
    lg.add('TEXT', r'[^#\*\n\[\]`!\-\~]+')

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

    @pg.production('document : elements')
    def document(p):
        return '<!DOCTYPE html><html><body>' + p[0] + '</body></html>'

    @pg.production('elements : element elements')
    def elements_many(p):
        return p[0] + p[1]


    @pg.production('elements : element')
    def elements_single(p):
        return p[0]

    @pg.production('element : HEADING text_content')
    def heading(p):
        level = len(p[0].getstr())
        return f'<h{level}>{p[1].getstr()}</h{level}>'

    @pg.production('element : text_contents')
    def text_contents_elem(p):
        return f"{p[0]}"

    @pg.production('element : separators')
    def separator_element(p):
        return p[0]

    @pg.production('separators : separator')
    def separator_single(p):
        return p[0]

    @pg.production('separators : separator separators')
    def separator_multiple(p):
        return "<br>"

    @pg.production('separator : NEWLINE')
    def separator_newline(p):
        return ""

    @pg.production('text_contents : text_content text_contents')
    def text_content_newline(p):
        return p[0] + p[1]

    @pg.production('text_contents : text_content')
    def single_text_contents(p):
        return p[0]

    @pg.production('text_content : TEXT')
    def text(p):
        return p[0].getstr()

    @pg.production('text_content : BOLD text_content BOLD')
    def bold_text(p):
        return f'<strong>{p[1]}</strong> '

    @pg.production('text_content : ITALIC text_content ITALIC')
    def italic_text(p):
        return f'<em>{p[1]}</em> '

    @pg.production('text_content : STRIKETHROUGH text_content STRIKETHROUGH')
    def strikethrough_text(p):
        return f'<del>{p[1]}</del> '

    @pg.production('text_content : LINK_OPEN text_content LINK_CLOSE URL')
    def link(p):
        return f'<a href="{p[3].getstr()[1:-1]}">{p[1].getstr()}</a>'

    @pg.production('element : IMAGE TEXT LINK_CLOSE URL')
    def image(p):
        return f'<img src="{p[3].getstr()[1:-1]}" alt="{p[1].getstr()}">'

    @pg.production('element : CODE_BLOCK TEXT CODE_BLOCK')
    def code_block(p):
        return f'<pre><code>{p[1].getstr()}</code></pre>'

    @pg.production('element : INLINE_CODE TEXT INLINE_CODE')
    def inline_code(p):
        return f'<code>{p[1].getstr()}</code>'

    @pg.error
    def error_handler(token):
        print(token)
        if token.gettokentype() == '$end':
            raise Exception("ERROR: Unexpected end of input")
        else:
            raise Exception("ERROR: Token type: {}, line: {}, column: {}".format(
                token.gettokentype(),
                token.getsourcepos().lineno,
                token.getsourcepos().colno))

    parser = pg.build()
    intermediate_representation = parser.parse(tokens_iter)
    return intermediate_representation


inp = """
This is ~cut~ text.

Hello
"""

output = parse_markdown(inp)
print(output)
file_path = "output.html"

# Open the file in write mode and write the HTML content to it
with open(file_path, "w") as html_file:
    html_file.write(output)




