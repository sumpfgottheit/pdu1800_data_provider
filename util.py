# Use acDevLibs for PyCharm Development from WarriorOfAvalon
# https://github.com/WarriorOfAvalon/AssettoCorsaDevLibs
try:
    import ac
except ImportError:
    from acDevLibs.acDev import ac as ac

def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

class Label:
    # INITIALIZATION

    def __init__(self, window, name, text=""):
        self.text = text
        self.name = name
        self.label_id = ac.addLabel(window, self.name)
        self.size = {"w": 0, "h": 0}
        self.pos = {"x": 0, "y": 0}
        self.color = (1, 1, 1, 1)
        self.bgColor = (0, 0, 0, 1)
        self.fontSize = 12
        self.align = "left"
        self.bgTexture = ""
        self.opacity = 1

    # PUBLIC METHODS

    def setText(self, text):
        self.text = text
        ac.setText(self.label_id, self.text)
        return self

    def setSize(self, w, h):
        self.size["w"] = w
        self.size["h"] = h
        ac.setSize(self.label_id, self.size["w"], self.size["h"])
        return self

    def setPos(self, x, y):
        self.pos["x"] = x
        self.pos["y"] = y
        ac.setPosition(self.label_id, self.pos["x"], self.pos["y"])
        return self

    def setColor(self, color):
        self.color = color
        ac.setFontColor(self.label_id, *self.color)
        return self

    def setFontSize(self, fontSize):
        self.fontSize = fontSize
        ac.setFontSize(self.label_id, self.fontSize)
        return self

    def setAlign(self, align="left"):
        self.align = align
        ac.setFontAlignment(self.label_id, self.align)
        return self

    def setBgTexture(self, texture):
        self.bgTexture = texture
        ac.setBackgroundTexture(self.label_id, self.bgTexture)
        return self

    def setBgColor(self, color):
        ac.setBackgroundColor(self.label_id, *color)
        return self

    def setBgOpacity(self, opacity):
        ac.setBackgroundOpacity(self.label_id, opacity)
        return self

    def setVisible(self, value):
        ac.setVisible(self.label_id, value)
        return self