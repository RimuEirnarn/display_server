# pylint: disable=all
import pygame
import sys
import html.parser
import random

# Core Window Elements
class Window:
    dragging_window = None  # Class-level lock

    def __init__(self, manager, title, x, y, width, height, flags=None):
        self.manager = manager
        self.title = title
        self.rect = pygame.Rect(x, y, width, height)
        self.min_size = (100, 50)
        self.max_size = (800, 600)
        self.resizable = True
        self.surface = pygame.Surface((width, height))
        self.children = []  # DOM elements
        self.focused = False
        self.flags = flags or {}
        self.titlebar_h = 24
        self.state = 0  # 0-normal,1-maximized,2-minimized
        self.dragging = False
        self.drag_offset = (0, 0)

    def render(self, screen):
        if self.state == 2:  # Minimized
            self._draw_titlebar(screen)
            return
        self.surface.fill((200, 200, 200))  # Clear surface first
        for elem in self.children:
            elem.render(self.surface)
        screen.blit(self.surface, self.rect.topleft)
        self._draw_titlebar(screen)

    def _draw_titlebar(self, screen):
        tb = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, self.titlebar_h)
        pygame.draw.rect(screen, (30, 30, 30), tb)
        font = pygame.font.SysFont(None, 16)
        text = font.render(self.title, True, (255, 255, 255))
        screen.blit(text, (self.rect.x + 5, self.rect.y + 4))

        # Buttons: Close, Maximize, Minimize
        self.close_rect = pygame.Rect(self.rect.right - 20, self.rect.y + 4, 16, 16)
        self.max_rect = pygame.Rect(self.rect.right - 40, self.rect.y + 4, 16, 16)
        self.min_rect = pygame.Rect(self.rect.right - 60, self.rect.y + 4, 16, 16)
        pygame.draw.rect(screen, (200, 50, 50), self.close_rect)
        pygame.draw.rect(screen, (50, 200, 50), self.max_rect)
        pygame.draw.rect(screen, (50, 50, 200), self.min_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                local = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                if local[1] < self.titlebar_h:
                    if self.close_rect.collidepoint(event.pos):
                        self.close()
                        return
                    elif self.max_rect.collidepoint(event.pos):
                        self.toggle_maximize()
                        return
                    elif self.min_rect.collidepoint(event.pos):
                        self.state = 2 if self.state != 2 else 0
                        return
                    if Window.dragging_window is None:
                        Window.dragging_window = self
                        self.dragging = True
                        self.drag_offset = (local[0], local[1])
                for elem in self.children:
                    if elem.rect.collidepoint(local):
                        elem.dispatch_event('click', event)

        elif event.type == pygame.MOUSEBUTTONUP:
            if Window.dragging_window == self:
                Window.dragging_window = None
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            if Window.dragging_window == self:
                new_x = event.pos[0] - self.drag_offset[0]
                new_y = event.pos[1] - self.drag_offset[1]
                self.rect.x = new_x
                self.rect.y = new_y

    def toggle_maximize(self):
        if self.state == 1:
            self.state = 0
            self.rect.size = (400, 300)
            self.rect.topleft = ((self.manager.screen.get_width() - 400) // 2,
                                  (self.manager.screen.get_height() - 300) // 2)
        else:
            self.state = 1
            self.rect.topleft = (0, 0)
            self.rect.size = (self.manager.screen.get_width(), self.manager.screen.get_height())

    def add_child(self, dom_elem):
        self.children.append(dom_elem)

    def close(self):
        self.manager.close_window(self)

# Simple DOM model
class DOMElement:
    def __init__(self, tag, attrs=None, styles=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.styles = styles or {}
        self.children = []
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.listeners = {}

    def append_child(self, elem):
        self.children.append(elem)

    def render(self, surface):
        bg = self.styles.get('background-color', None)
        if bg:
            surface.fill(pygame.Color(bg), self.rect)
        for child in self.children:
            child.render(surface)

    def dispatch_event(self, name, event):
        if name in self.listeners:
            self.listeners[name](event)

    def add_event_listener(self, name, callback):
        self.listeners[name] = callback

# Lightweight HTML parser
class SimpleHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.root = None

    def handle_starttag(self, tag, attrs):
        styles = {}
        attr_dict = dict(attrs)
        if 'style' in attr_dict:
            for decl in attr_dict['style'].split(';'):
                if ':' in decl:
                    k, v = decl.split(':', 1)
                    styles[k.strip()] = v.strip()
        elem = DOMElement(tag, attrs=attr_dict, styles=styles)
        if not self.stack:
            self.root = elem
        else:
            self.stack[-1].append_child(elem)
        self.stack.append(elem)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_data(self, data):
        pass

# Window Manager
class WindowManager:
    def __init__(self, size=(1024, 768)):
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption('Pygame Display Server')
        self.windows = []
        self.clock = pygame.time.Clock()
        self.running = True

    def create_window(self, title, width=400, height=300, flags=None):
        x = (self.screen.get_width() - width) // 2
        y = (self.screen.get_height() - height) // 2
        w = Window(self, title, x, y, width, height, flags)
        self.windows.append(w)
        return w

    def close_window(self, window):
        if window in self.windows:
            self.windows.remove(window)

    def mainloop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for w in self.windows:
                    w.handle_event(event)
            self.screen.fill((50, 50, 50))
            for w in sorted(self.windows, key=lambda x: x.rect.y):
                w.render(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

def push(manager: WindowManager, title, width, height):
    win = manager.create_window(title)
    data = '<div style="background-color:#444444;width:100%;height:100%"></div>'
    parser = SimpleHTMLParser()
    parser.feed(data)
    win.add_child(parser.root)
    return win

# Example usage
if __name__ == '__main__':
    manager = WindowManager()
    # win = manager.create_window('Test App', 400, 300)
    # parser = SimpleHTMLParser()
    # parser.feed(html_data)
    # win.add_child(parser.root)
    windows = []
    for base in [("Test App", 400, 300), ("Test App 2", 800, 600)]:
        windows.append(push(manager, *base))
    manager.mainloop()
