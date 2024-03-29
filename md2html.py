import argparse
import os
from rply import LexerGenerator, ParserGenerator
import warnings

def parse_markdown(program):
    lg = LexerGenerator()
    lg.add('HEADING', r'\#{1,6} ')
    lg.add('BOLD', r'\*\*|\_\_')
    lg.add('ASTERISK_OR_UNDERSCORE', r'\*|_')
    lg.add('STRIKETHROUGH', r'\~\~')
    lg.add('CODE_BLOCK', r'(?s)\`\`\`(.*?)\`\`\`')
    lg.add('INLINE_CODE',  r'(?s)\`(.*?)\`')
    lg.add('LINK_OPEN', r'\[')
    lg.add('LINK_CLOSE', r'\]')
    lg.add('IMAGE', r'\!\[')
    lg.add('URL', r'\([^\)]+\)')
    lg.add('LIST_BULLET', r'\+(?=\s)|\-(?=\s)')
    lg.add('LIST_NUMBER', r'\d+\.(?![^\s])')
    lg.add('BLOCKQUOTE', r'\>')
    lg.add('NEWLINE', r'\n')
    lg.add('OPEN_PARENS', r'\(')
    lg.add('CLOSE_PARENS', r'\)')
    lg.add('TEXT', r'[^#\*\n\[\]`!\~\_]+|[#][^ ]+|[\-\+\*][^ ]+')

    lg.ignore(r'[ \t]+')

    lexer = lg.build()

    tokens_iter = lexer.lex(program)

    possible_tokens = [rule.name for rule in lexer.rules]

    pg = ParserGenerator(possible_tokens,
                           precedence=[
                               ('left', ['BOLD', 'ASTERISK_OR_UNDERSCORE']),
                               ('left', ['LINK_OPEN', 'LINK_CLOSE', 'IMAGE', 'URL']),
                               ('left', ['CODE_BLOCK', 'INLINE_CODE']),
                               ('left', ['BLOCKQUOTE', 'LIST_BULLET', 'LIST_NUMBER']),
                               ('left', ['NEWLINE']),
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
        level = len(p[0].getstr())-1
        return f'<h{level}>{p[1]}</h{level}>'

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

    @pg.production('text_content : ASTERISK_OR_UNDERSCORE text_content ASTERISK_OR_UNDERSCORE')
    def italic_text(p):
        return f'<em>{p[1]}</em> '

    @pg.production('text_content : STRIKETHROUGH text_content STRIKETHROUGH')
    def strikethrough_text(p):
        return f'<del>{p[1]}</del> '

    @pg.production('text_content : LINK_OPEN text_content LINK_CLOSE URL')
    def link(p):
        return f'<a href="{p[3].getstr()[1:-1]}">{p[1]}</a>'

    @pg.production('text_content : LINK_OPEN text_content LINK_CLOSE OPEN_PARENS CLOSE_PARENS')
    def link(p):
        return f'<a href="">{p[1]}</a> '

    @pg.production('element : IMAGE TEXT LINK_CLOSE URL')
    def image(p):
        return f'<img src="{p[3].getstr()[1:-1]}" alt="{p[1].getstr()}">'

    @pg.production('element : CODE_BLOCK')
    def code_block(p):
        code_content = p[0].getstr()[3:-3]
        # Escape HTML special characters
        code_content = code_content.replace('&', '&amp;')
        code_content = code_content.replace('<', '&lt;')
        code_content = code_content.replace('>', '&gt;')
        code_content = code_content.replace('"', '&quot;')
        code_content = code_content.replace("'", '&#39;')
        return f'<pre><code>{code_content}</code></pre>'

    @pg.production('element : INLINE_CODE')
    def inline_code(p):
        code_content = p[0].getstr()[1:-1]
        # Escape HTML special characters
        code_content = code_content.replace('&', '&amp;')
        code_content = code_content.replace('<', '&lt;')
        code_content = code_content.replace('>', '&gt;')
        code_content = code_content.replace('"', '&quot;')
        code_content = code_content.replace("'", '&#39;')
        return f'<code>{code_content}</code>'


    @pg.production('bulleted_list_item : LIST_BULLET text_contents')
    @pg.production('bulleted_list_item : ASTERISK_OR_UNDERSCORE text_contents')
    def bulleted_list_item(p):
        return f'<li>{p[1]}</li>'

    @pg.production('numbered_list_item : LIST_NUMBER text_contents')
    def numbered_list_item(p):
        return f'<li>{p[1]}</li>'

    @pg.production('bulleted_list : bulleted_list_item separators bulleted_list')
    def build_bulleted_list_multiple(p):
        p[2].append(p[0])
        return p[2]

    @pg.production('bulleted_list : bulleted_list_item separators')
    def build_bulleted_list(p):
        return [p[0]]

    @pg.production('numbered_list : numbered_list_item separators numbered_list')
    def build_numbered_list_multiple(p):
        p[2].append(p[0])
        return p[2]

    @pg.production('numbered_list : numbered_list_item separators')
    def build_numbered_list(p):
        return [p[0]]

    @pg.production('element : bulleted_list')
    def bulleted_list_element(p):
        return f'<ul>{"".join(p[0])}</ul>'

    @pg.production('element : numbered_list')
    def numbered_list_element(p):
        return f'<ol>{"".join(p[0])}</ol>'

    @pg.production('blockquote_line : BLOCKQUOTE text_contents')
    def blockquote_line(p):
        return p[1]

    @pg.production('blockquote : blockquote_line separators blockquote')
    def extend_blockquote(p):
        # Extend the existing blockquote with a new line
        p[2].append("<br>")
        p[2].append(p[0])
        return p[2]

    @pg.production('blockquote : blockquote_line separators')
    def start_blockquote(p):
        return [p[0]]

    @pg.production('element : blockquote')
    def blockquote_element(p):
        # Join all blockquote lines and wrap in <blockquote>
        blockquote_content = ''.join(p[0])
        return f'<blockquote>{blockquote_content}</blockquote>'

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
    html_md = parser.parse(tokens_iter)
    return html_md

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert Markdown to HTML")
    parser.add_argument("md_file", help="Path to the Markdown file")
    warnings.filterwarnings("ignore")

    # Parse arguments
    args = parser.parse_args()

    md_file = args.md_file

    if not md_file.endswith('.md'):
        raise ValueError("File must have a .md extension")

    md_content = ""
    with open(md_file, 'r') as file:
        md_content = file.read()

    html_content = parse_markdown(md_content)

    # Create HTML file path
    base_name = os.path.splitext(md_file)[0]
    html_file_path = base_name + '.html'

    # Write HTML content to a new file
    with open(html_file_path, 'w') as file:
        file.write(html_content)
        print("Markdown file has been converted to HTML.")
