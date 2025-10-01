
def controls_alias_hack(ppd):
     tokens = ppd.alias.split()
     ppd.alias = " ".join(tokens[:-1] + [tokens[-1].zfill(2)])
