class FlowCommand(object):
    def __init__(self,s):
        self.command = 'UnsupportedCommand'
        self.port_id = -1
        self.flow_id = -1
        self.attr = None
        self.patterns = None
        self.actions = None
        self.origin = s

    def build(self):
        s = self.origin
        s = s.split()
        self.command = s[0]

        try:
            self.port_id = int(s[1])
        except Exception:
            return False

        p_begin = self.origin.find('pattern')
        a_begin = self.origin.find('actions')

        if p_begin == -1 or a_begin == -1:
            if len(s) == 2:
                return  (s[0] in ('flush','list'))

            if len(s) != 4:
                return False

            if self.command == 'query':
                ## ignore 'count'
                try:
                    self.flow_id = int(s[2])
                except Exception:
                    return False

            if self.command == 'destroy':
                try:
                    self.flow_id = int(s[3])
                except Exception:
                    return False
                return s[2] == 'rule'

            return False

        ## create or validate
        if self.command not in('create','validate'):
            return False

        if p_begin > a_begin:
            return False

        attr_b = self.origin.find(s[2])
        self.attr = self.origin[attr_b:p_begin].strip()

        p_begin += len('pattern')

        p_end = self.origin.find('end',p_begin,a_begin)
        a_begin += len('actions')
        a_end = self.origin.find('end',a_begin)
        if p_end == -1 or a_end == -1:
            return False

        patterns = [p.strip()  for p in self.origin[p_begin:p_end].split('/')]
        actions = [a.strip()  for a in self.origin[a_begin:a_end].split('/')]

        if len(patterns) == 0:
            return False

        self.patterns = patterns
        self.actions = actions
        return True
