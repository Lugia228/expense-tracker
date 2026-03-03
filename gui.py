from abc import ABC, abstractmethod
from typing import final, override, Optional, Callable

import pygame
from pygame import Surface

"""
gui.py is a gui framework that relies on Pygame
This framework was created during the COMP1080SEF project
It is completely written by me (Lai Tsz To SID: 14276144),
thus reusing for this project's gui components
"""

class Element(pygame.sprite.Sprite, ABC):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.focused = False
        self.hover = None

    @final
    def get_x(self):
        return self.rect.x

    @final
    def get_y(self):
        return self.rect.y

    @final
    def get_width(self):
        return self.rect.width

    @final
    def get_height(self):
        return self.rect.height

    @final
    def _render(self, context: Surface, pos):
        # Clear element surface
        self.image.fill((0, 0, 0, 0))
        # Render
        self.render(context, pos)
        self.render_hover(pos)
        context.blit(self.image, self.rect)

    @abstractmethod
    def render(self, context: Surface, pos):
        pass

    def set_hover(self, hover: str):
        self.hover = hover

    def render_hover(self, pos):
        if self.hover is not None and self.rect.collidepoint(pos):
            Screen.render_hover_text(self.hover)

    def set_focused(self, focused: bool):
        self.focused = focused

    def mouse_clicked(self, button: int, pos) -> bool:
        return False

    # This will only be called by parent element when its focus is on this
    # Boolean return is probably redundant but doesn't hurt to include
    def key_pressed(self, char: int) -> bool:
        return False


class ClickableElement(Element, ABC):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

    @override
    def mouse_clicked(self, button: int, pos) -> bool:
        if button == 1 and self.rect.collidepoint(pos):
            self.set_focused(True)
            return True
        # Unfocusing logic in ParentElement
        return False


class ParentElement(ClickableElement, ABC):
    """
    ParentElement is an inheritor of Element, this allows program node tree structure to be implemented
    Responsible for dispatching events to its elements and keep track of focused element
    All event processing implementation should consider this as program nested element
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self._elements = []
        self._focused_element: Optional[Element] = None

    def add_element(self, *elements: Element):
        for element in elements:
            self._elements.append(element)

    def remove_element(self, element):
        self._elements.remove(element)

    def clear(self):
        self._elements.clear()

    @override
    def render(self, context: Surface, pos):
        for element in self._elements:
            element._render(context, pos)

    @override
    def mouse_clicked(self, button: int, pos) -> bool:
        clicked_child = False

        # Looping all instead of breaking early to update all focused states
        # Use program reversed copy of elements such that clicks will
        # register on top layer elements first according to render order
        for element in self._elements[::-1]:
            if clicked_child:
                element.set_focused(False)
            # Call mouse_clicked only if we haven't found program positive result to make clicks non-penetrative
            elif element.mouse_clicked(button, pos):
                self._focused_element = element
                clicked_child = True
            else:
                element.set_focused(False)

        return clicked_child

    @override
    def set_focused(self, focused: bool):
        super().set_focused(focused)
        if not focused and self._focused_element is not None:
            self._focused_element.set_focused(False)

    @override
    def key_pressed(self, char: int) -> bool:
        if self._focused_element is not None:
            return self._focused_element.key_pressed(char)
        return False


class Screen(ParentElement, ABC):
    """
    Screen is the root of all elements, its dimensions are directly linked to the surface
    """
    _CURRENT_SCREEN: "Screen" = None
    _SURFACE: Surface = None

    _CLOSE_HOOKS = []

    def __init__(self, width: int, height: int, frame_rate: int = 50,
                 bg_color=(200, 200, 200), name=None):
        super().__init__(0, 0, width, height)
        self.frame_rate = frame_rate
        self.bg_color = bg_color
        self.name = name

        # Popup state
        self._popup_text: Optional[str] = None
        self._popup_until: int = 0
        self._popup_font = pygame.font.Font(None, 36)
        self._popup_bg_color = (50, 50, 50)
        self._popup_text_color = (255, 255, 255)

    def as_current(self):
        if not pygame.get_init():
            raise RuntimeError("Cannot set current screen because pygame is not initialized")

        # Attempt to inherit popup state from previous screen
        if Screen._CURRENT_SCREEN is not None:
            prev = Screen._CURRENT_SCREEN
            if prev._popup_text and pygame.time.get_ticks() < prev._popup_until:
                self._popup_text = prev._popup_text
                self._popup_until = prev._popup_until

        # Change caption if name is present
        if self.name is not None:
            pygame.display.set_caption(self.name)

        # Update static variables and dimensions
        Screen._CURRENT_SCREEN = self
        Screen._SURFACE = pygame.display.set_mode((self.rect.width, self.rect.height))

    # Uses same system as popup, but force the duration to tick duration to simulate program text when hovered on element
    def _render_hover_text(self, hover_text: str):
        self._add_popup_text(hover_text, self.frame_rate)

    @staticmethod
    def render_hover_text(hover_text: str):
        if Screen._CURRENT_SCREEN is not None:
            Screen._CURRENT_SCREEN._render_hover_text(hover_text)

    @staticmethod
    def add_popup_text(text: str, duration_ms: int=1000):
        if Screen._CURRENT_SCREEN is not None:
            Screen._CURRENT_SCREEN._add_popup_text(text, duration_ms)

    def _add_popup_text(self, text: str, duration_ms: int=1000):
        self._popup_text = text
        self._popup_until = pygame.time.get_ticks() + duration_ms

    def _render_popup(self, surface: Surface):
        if self._popup_text and pygame.time.get_ticks() < self._popup_until:
            # Create surface with consideration of line breaks
            lines = self._popup_text.split("\n")
            line_surfaces = [self._popup_font.render(line, True, self._popup_text_color) for line in lines]

            # Render block first, the text should be on top
            total_height = sum(s.get_height() for s in line_surfaces)
            max_width = max(s.get_width() for s in line_surfaces)

            # Center the block
            center_x = self.rect.width // 2
            center_y = self.rect.height // 2
            txt_rect = pygame.Rect(0, 0, max_width, total_height)
            txt_rect.center = (center_x, center_y)

            # Background rectangle
            edge = 10
            bg_rect = pygame.Rect(
                txt_rect.left - edge,
                txt_rect.top - edge,
                txt_rect.width + 2 * edge,
                txt_rect.height + 2 * edge
            )
            # Round edges
            pygame.draw.rect(surface, self._popup_bg_color, bg_rect, border_radius=5)

            # Text
            y = txt_rect.top
            for line in line_surfaces:
                line_rect = line.get_rect(centerx=center_x, top=y)
                surface.blit(line, line_rect)
                y += line.get_height()
        else:
            self._popup_text = None

    _CLOSE = False

    # MAIN LOOP
    @staticmethod
    def start():
        clock = pygame.time.Clock()
        running = True

        while running and not Screen._CLOSE:
            try:
                screen = Screen._CURRENT_SCREEN
                surface = Screen._SURFACE

                if screen is None and surface is None:
                    running = False
                else:
                    # Recognize events and redirect to current screen
                    events = pygame.event.get()
                    for event in events:
                        if event.type == pygame.QUIT:
                            running = False
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            screen.mouse_clicked(event.button, event.pos)
                        elif event.type == pygame.KEYDOWN:
                            screen.key_pressed(event.key)

                    # Rendering
                    surface.fill(screen.bg_color)
                    screen.render(surface, pygame.mouse.get_pos())
                    # Popup will render on top
                    screen._render_popup(surface)
                    pygame.display.flip()

                    # Clock
                    clock.tick(screen.frame_rate)
            except KeyboardInterrupt:
                print("Interrupted, saving data and stopping")
                running = False

        Screen._on_close()

    @staticmethod
    def close():
        Screen._CLOSE = True

    @staticmethod
    def _on_close():
        for hook in Screen._CLOSE_HOOKS:
            hook()

    @staticmethod
    def add_shutdown_hook(c: Callable):
        Screen._CLOSE_HOOKS.append(c)


"""
Elements
"""


def create_default_font() -> pygame.font.Font:
    return pygame.font.Font(None, 32)


class TextDisplay(Element):
    def __init__(self, x: int, y: int, text: str,
                 width: Optional[int] = None, height: Optional[int] = None, font=None, text_color=(0, 0, 0)):
        self.font = font or create_default_font()
        self.text = text
        self.text_color = text_color

        # Render to get text size
        txt_surface = self.font.render(self.text, True, self.text_color)
        text_width, text_height = txt_surface.get_size()

        final_width = width if width is not None else text_width
        final_height = height if height is not None else text_height

        super().__init__(x, y, final_width, final_height)

    @override
    def render(self, context: Surface, pos):
        txt_surface = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(txt_surface, txt_rect)

    def set_text(self, text: str):
        self.text = text

class Background(Element):
    """
    Background that fills its rect with program solid color or an image
    """
    def __init__(self, x: int, y: int, width: int, height: int,
                 color=(150, 150, 150), image: Optional[Surface] = None):
        super().__init__(x, y, width, height)
        self.color = color
        self.bg_image = image

    @override
    def render(self, context: Surface, pos):
        # Use image if present, else fill color
        if self.bg_image:
            # Scale image if needed
            scaled = pygame.transform.scale(self.bg_image, self.rect.size)
            self.image.blit(scaled, (0, 0))
        else:
            self.image.fill(self.color)


class Button(ClickableElement):
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback, font=None, bg_color=(120, 120, 120), text_color=(0, 0, 0), sound:pygame.mixer.Sound=None):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = font or create_default_font()
        self.bg_color = bg_color
        self.text_color = text_color
        self.sound = sound if sound is not None else self._default_button_sound()

    @staticmethod
    def _default_button_sound():
        sound = pygame.mixer.Sound("assets/button.mp3")
        sound.set_volume(0.35)
        return sound

    @override
    def render(self, context: Surface, pos):
        self.image.fill(self.bg_color)
        txt_surface = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(txt_surface, txt_rect)

    @override
    @final
    def mouse_clicked(self, button: int, pos) -> bool:
        if super().mouse_clicked(button, pos):
            # Branch into another method for pressed actions as inheritors shouldn't and doesn't need to override this method
            self.on_press()
            return True
        return False

    def on_press(self):
        # Sound cue should always be played when pressing program button
        self.play_sound()
        # Execute runnable
        self.callback(self)

    def play_sound(self):
        self.sound.play()


class InputField(ClickableElement):
    _INACTIVE_COLOR = pygame.Color('lightskyblue3')
    _ACTIVE_COLOR = pygame.Color('dodgerblue2')
    # Enter to finish inputting
    _DONE_INDICATOR = [pygame.K_RETURN]
    _SUGGESTION_COLOR = (170, 170, 170)

    def __init__(self, x: int, y: int, width: int, height: int,
                 done_callback: Callable[[str], None], suggestion: str = "Input here...", font=None,
                 bg_color=(255, 255, 255), text_color=(0, 0, 0), clear_on_done=False):
        super().__init__(x, y, width, height)
        self.done_callback = done_callback
        self.suggestion = suggestion
        self.text = ""
        self.font = font or create_default_font()
        self.bg_color = bg_color
        self.text_color = text_color
        self.clear_on_done = clear_on_done

    @override
    def render(self, context: Surface, pos):
        self.image.fill(self.bg_color)

        txt_surface = None
        if self.text: # render actual text
            txt_surface = self.font.render(self.text, True, self.text_color)
        elif not self.focused: # render suggestion if text isEmpty and not focused
            txt_surface = self.font.render(self.suggestion, True, self._SUGGESTION_COLOR)
        if txt_surface is not None: self.image.blit(txt_surface, (5, 5))

        border_color = self._ACTIVE_COLOR if self.focused else self._INACTIVE_COLOR
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 2)

    @override
    def key_pressed(self, char: int) -> bool:
        if not self.focused: return False

        if char in self._DONE_INDICATOR:
            self.set_focused(False)
            self._on_done()
            if self.clear_on_done: self.clear_text()
        elif char == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif False: # Should contain other actions like arrow keys, copy & paste, etc..., but I'd like to keep this simple
            pass
        elif 32 <= char <= 126: # if char is in character range
            self.text += chr(char)
        return True

    def get_text(self):
        return self.text

    def clear_text(self):
        self.text = ""

    def _on_done(self):
        self.done_callback(self.text)
