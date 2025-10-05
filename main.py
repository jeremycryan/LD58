import math

import pygame

import constants as c
import frame as f
import sys

from primitives import Pose
from sound_manager import SoundManager
from image_manager import ImageManager
import asyncio

import webbrowser


class Game:
    def __init__(self):
        pygame.init()
        SoundManager.init()
        ImageManager.init()
        self.small_screen = pygame.Surface(c.WINDOW_SIZE)
        self.screen = pygame.display.set_mode(c.SCALED_WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        pygame.mixer.init()

        pygame.mixer.music.load("assets/sounds/music.wav")
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

        self.shake_amp = 0
        self.since_shake = 999
        self.reset()
        self.current_level = 0

        pygame.display.set_caption(f"{c.CAPTION}")

        asyncio.run(self.main())

    def shake(self, amt=15):
        self.shake_amp = amt
        self.since_shake = 0

    @staticmethod
    def is_web_build():
        return sys.platform == "emscripten"

    def open_steam_page(self):
        if not self.is_web_build():
            webbrowser.open('https://store.steampowered.com/app/3284290/Moonsigil_Atlas/')
        else:
            webbrowser.open('https://store.steampowered.com/app/3284290/Moonsigil_Atlas/')

    def get_shake_offset(self):
        magnitude = math.cos(self.since_shake * 50) * self.shake_amp
        direction = Pose((1, 1))
        if abs(magnitude) < 0.25:
            magnitude = 0
        return direction * magnitude

    def reset(self):
        pass

    async def main(self):
        current_frame = f.MainFrame(self)
        current_frame.load()
        self.clock.tick(60)

        while True:
            dt, events = self.get_events()
            if dt == 0:
                dt = 1/100000
            if dt > 0.05:
                dt = 0.05
            current_frame.update(dt, events)
            current_frame.draw(self.small_screen, self.get_shake_offset().get_position())
            scaled = pygame.transform.scale(self.small_screen, c.SCALED_WINDOW_SIZE)
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
            await asyncio.sleep(0)

            if current_frame.done:
                current_frame = current_frame.next_frame()
                current_frame.load()


    def get_events(self):

        dt = self.clock.tick(c.FRAMERATE)/1000

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self.since_shake += dt
        self.shake_amp -= 5*dt
        self.shake_amp *= 0.001 ** dt
        if (self.shake_amp < 0):
            self.shake_amp = 0

        return dt, events


if __name__ == "__main__":
    Game()
