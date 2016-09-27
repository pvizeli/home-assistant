"""Template engine for Home-Assistant."""
import re


class TemplateEngine(object):

    autowrite = re.compile('(^[\'\"])|(^[a-zA-Z0-9_\[\]\'\"]+$)')
    delimiters = ('{%', '%}')
    delimiters_var = ('{{', '}}')

    def __init__(self):
        """Init TemplateEngine."""
        self._code = None
        self._cache = {}
        self.filter = {}

    def compile(self, text):
        key = hash(text)
        if key in self._cache:
            self._code = self._cache.get(key)
            return

        # compile
        self._cache[key] = self._code = self._compile(text)

    def _compile(self, source):
        offset = 0
        tokens = ['# -*- coding: utf-8 -*-']
        start, end = self.delimiters
        escaped = (re.escape(start), re.escape(end))
        regex = re.compile('%s(.*?)%s' % escaped, re.DOTALL)
        for i, part in enumerate(regex.split(source)):
            print("%i -> %s", i, part)
            part = part.replace('\\'.join(start), start)
            part = part.replace('\\'.join(end), end)
            if i % 2 == 0:
                if not part:
                    continue
                part = part.replace('\\', '\\\\').replace('"', '\\"')
                part = '\t' * offset + 'write("""%s""")' % part
            else:
                part = part.rstrip()
                if not part:
                    continue
                part_stripped = part.lstrip()
                if part_stripped.startswith(':'):
                    if not offset:
                        raise SyntaxError('no block statement to terminate: ${%s}$' % part)
                    offset -= 1
                    part = part_stripped[1:]
                    if not part.endswith(':'):
                        continue
                elif self.autowrite.match(part_stripped):
                    part = 'write(%s)' % part_stripped
                lines = part.splitlines()
                margin = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
                part = '\n'.join('\t' * offset + l[margin:] for l in lines)
                if part.endswith(':'):
                    offset += 1
            tokens.append(part)
        if offset:
            raise SyntaxError('%i block statement(s) not terminated' % offset)
        print("%s", tokens)
        return compile('\n'.join(tokens), '<string>', 'exec')

    def render(self, **namespace):
        """Renders the template according to the given namespace."""
        stack = []

        def write(*args):
            for value in args:
                if not isinstance(value, str):
                    value = str(value, 'utf-8')
                stack.append(value)
        namespace['write'] = write
        # execute template code
        exec(self._code, namespace)
        return ''.join(stack)
