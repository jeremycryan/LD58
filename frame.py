import math
import time

import pygame

from image_manager import ImageManager
import constants as c
from primitives import Pose
from sound_manager import SoundManager


class Frame:
    def __init__(self, game):
        self.game = game
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((128, 128, 128))

    def next_frame(self):
        return Frame(self.game)

    def name(self):
        return self.__class__.__name__


class TitleFrame(Frame):
    def load(self):
        pass

    def update(self, dt, events):

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.done = True

    def draw(self, surface, offset=(0, 0)):
        surface.fill((255, 255, 255))

    def next_frame(self):
        return MainFrame

class MainFrame(Frame):
    class Level:
        def __init__(self, destination_position, start_position, level_surface, level_background, pickups, line_lengths):
            self.destination_position = destination_position
            self.start_position = start_position
            self.level_surface = level_surface
            self.level_background = level_background
            self.pickups = pickups
            self.line_lengths = line_lengths

    def load(self):
        self.levels = [
            MainFrame.Level(
                (47, 35),
                (110, 110),
                ImageManager.load("assets/images/level_1.png"),
                ImageManager.load("assets/images/level_1_background.png"),
                [],
                [75, 75]
            ),
            MainFrame.Level(
                (46, 21),
                (26, 41),
                ImageManager.load("assets/images/level_2.png"),
                ImageManager.load("assets/images/level_1_background.png"),
                [(120, 116)],
                [85, 85, 62, 62, 62]
            ),
            MainFrame.Level(
                (22, 129),
                (81, 72),
                ImageManager.load("assets/images/level_3.png"),
                ImageManager.load("assets/images/level_1_background.png"),
                [(80, 15), (144, 86)],
                [55, 18, 60, 65, 25, 100, 40, 25]
            ),
            MainFrame.Level(
                (140, 19),
                (122, 38),
                ImageManager.load("assets/images/level_4.png"),
                ImageManager.load("assets/images/level_1_background.png"),
                [(17, 22), (55, 53), (147, 134)],
                [30, 60, 60, 40, 90, 30, 30, 30, 75, 52, 35, 95]
            ),
            MainFrame.Level(
                (15, 129),
                (15, 15),
                ImageManager.load("assets/images/level_1.png"),
                ImageManager.load("assets/images/level_1_background.png"),
                [],
                [157, 157, 157, 157, 147]
            ),
        ]
        self.won = False
        self.level_index = 0
        self.load_active_level(self.levels[self.level_index])

        self.since_victory_shown = 99999
        self.new_level_loaded = True
        self.level_complete_surf = ImageManager.load("assets/images/level_complete.png")
        self.completely_won = False
        self.you_win = ImageManager.load("assets/images/you_win.png")

        self.place_sound = SoundManager.load("assets/sounds/placement.wav")
        self.pickup_sound = SoundManager.load("assets/sounds/pickup.wav")
        self.cant_place_sound = SoundManager.load("assets/sounds/cantplace.wav")
        self.beat_level_sound = SoundManager.load("assets/sounds/nextlevel.wav")

    def advance_level(self):
        self.won = False
        self.new_level_loaded = True
        self.level_index += 1
        if self.level_index > len(self.levels) - 1:
            self.completely_won = True
            return
        self.load_active_level(self.levels[self.level_index])

    def draw_victory_message(self, surface, offset=(0, 0)):
        appear_time = 0.3
        stick_time = 1
        disappear_time = 0.3
        alpha = 0
        xoff = offset[0]
        yoff = offset[1]
        if (self.since_victory_shown < appear_time):
            alpha = self.since_victory_shown/appear_time * 255
            yoff = (1 - alpha/255)**2 * 35
        elif self.since_victory_shown < appear_time + stick_time or not self.new_level_loaded:
            if (not self.new_level_loaded):
                self.advance_level()
            alpha = 255
        elif self.since_victory_shown < appear_time + stick_time + disappear_time:
            since_start_disappear = self.since_victory_shown - appear_time - stick_time
            alpha = 255 - since_start_disappear/disappear_time * 255
            yoff = (1 - alpha/255)**2 * -35
        color = 5, 27, 45
        back_surf = pygame.Surface(c.WINDOW_SIZE)
        back_surf.fill(color)
        back_surf.set_alpha(alpha)
        if (self.completely_won):
            surface.blit(self.you_win, (0, 0))
        surface.blit(back_surf, (0, 0))
        self.level_complete_surf.set_alpha(alpha)
        level_complete_surf = pygame.transform.rotate(self.level_complete_surf, abs(yoff) * 1)
        surface.blit(level_complete_surf,
                     (c.WINDOW_WIDTH//2 - level_complete_surf.get_width()//2 + xoff,
                      c.WINDOW_HEIGHT//2 - level_complete_surf.get_height()//2 + yoff))


    def load_active_level(self, level):
        self.active_level = level
        self.points_placed = [self.active_level.start_position]
        self.level_lines = self.active_level.line_lengths
        self.destination_position = self.active_level.destination_position
        self.level_surface = self.active_level.level_surface
        self.level_surface_dark = self.level_surface.copy()
        black = self.level_surface_dark.copy()
        black.fill((0, 0, 0))
        self.level_surface_dark.blit(black, (0, 0), special_flags=pygame.BLEND_MULT)
        self.level_background = self.active_level.level_background
        self.cursor_surf = ImageManager.load("assets/images/cursor.png")
        self.cursor_surf.set_colorkey((0, 0, 0))
        self.start_point_surf = ImageManager.load("assets/images/start_point.png")
        self.mid_point_surf = ImageManager.load("assets/images/regular_point.png")
        self.frame = ImageManager.load("assets/images/frme.png")
        self.destination_surface = ImageManager.load("assets/images/destination_unlocked.png")
        self.destination_surface_locked = ImageManager.load("assets/images/destination_locked.png")
        self.pickups = self.active_level.pickups
        self.pickups_per_move = []
        self.destination_radius = 8
        self.pickup_radius = 5
        self.pickup_surface = ImageManager.load("assets/images/pickup.png")

    def update(self, dt, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.attempt_place_point()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.undo()
                if event.key == pygame.K_r:
                    self.reset()
                if event.key == pygame.K_ESCAPE:
                    self.done = True
        if self.won and self.new_level_loaded:
            self.new_level_loaded = False
            self.since_victory_shown = 0
            self.beat_level_sound.play()
        self.since_victory_shown += dt

    def undo(self):
        if self.won:
            return False
        if len(self.points_placed) > 1:
            self.points_placed = self.points_placed[:-1]
            self.pickups_per_move = self.pickups_per_move[:-1]
            return True
        return False

    def reset(self):
        if self.won:
            return False
        while self.undo():
            continue

    def draw(self, surface, offset=(0, 0)):
        surface.fill((5, 27, 45))

        lx = c.LEVEL_POSITION[0] + offset[0]
        ly = c.LEVEL_POSITION[1] + offset[1]
        surface.blit(self.level_background, (lx, ly))
        self.draw_destination(surface, offset)
        self.draw_pickups(surface, offset)
        surface.blit(self.level_surface_dark, (lx, ly + 1))
        surface.blit(self.level_surface, (lx, ly))
        self.draw_points(surface, offset)
        surface.blit(self.frame, (offset[0], offset[1]))
        self.draw_mouse_cursor(surface, offset)
        self.draw_lines(surface, offset)
        self.draw_victory_message(surface, offset)

    def destination_unlocked(self):
        remaining_pickups = self.pickups.copy()
        for move in self.pickups_per_move:
            for pickup in move:
                if pickup in remaining_pickups:
                    remaining_pickups.remove(pickup)
        return len(remaining_pickups) == 0

    def draw_destination(self, surface, offset=(0, 0)):
        xoff, yoff = offset
        if (self.destination_unlocked()):
            yoff += math.sin(time.time() * 10) * 1
        dest_surf = self.destination_surface if self.destination_unlocked() else self.destination_surface_locked
        pos = self.destination_position[0] + xoff + c.LEVEL_POSITION[0] - self.destination_surface.get_width()//2, \
              self.destination_position[1] + yoff + c.LEVEL_POSITION[1] - self.destination_surface.get_height()//2
        surface.blit(dest_surf, (pos))

    def draw_pickups(self, surface, offset=(0, 0)):
        for pickup in self.remaining_pickups():
            x, y = pickup
            x += offset[0] + c.LEVEL_POSITION[0] - self.pickup_surface.get_width()//2
            y += offset[1] + c.LEVEL_POSITION[1] - self.pickup_surface.get_height()//2
            surface.blit(self.pickup_surface, (x, y))


    def next_frame(self):
        return MainFrame(self.game)

    def mouse_in_play_area(self):
        mpos = pygame.mouse.get_pos()
        if mpos[0] < c.LEVEL_POSITION[0] * c.WINDOW_SCALE or mpos[0] > (c.LEVEL_POSITION[0] + c.LEVEL_SIZE[0])*c.WINDOW_SCALE:
            return False
        if mpos[1] < c.LEVEL_POSITION[1] * c.WINDOW_SCALE or mpos[1] > (c.LEVEL_POSITION[1] + c.LEVEL_SIZE[1]) * c.WINDOW_SCALE:
            return False
        return True

    def next_line_length(self):
        if len(self.points_placed) <= len(self.level_lines):
            return self.level_lines[len(self.points_placed) - 1]
        return None

    def cursor_position_scaled(self):
        mpos = pygame.mouse.get_pos()
        return mpos[0] / c.WINDOW_SCALE, mpos[1] / c.WINDOW_SCALE

    def destination_position_scaled_level_space(self):
        if (self.next_line_length()) == None:
            return (0, 0)
        start = self.points_placed[-1]
        mpos = self.cursor_position_scaled()
        mpos = mpos[0] - c.LEVEL_POSITION[0], mpos[1] - c.LEVEL_POSITION[1]
        dx = mpos[0] - start[0]
        dy = mpos[1] - start[1]
        if dx == 0:
            dx = 1  # avoid zero division
        line = Pose((dx, dy))
        line.scale_to(self.next_line_length())
        end = start[0] + int(line.x), start[1] + int(line.y)
        return end

    def draw_mouse_cursor(self, surface, offset=(0, 0)):
        return
        if not self.mouse_in_play_area():
            return # TODO cursor outside

        mpos = pygame.mouse.get_pos()
        surface.blit(self.cursor_surf, (mpos[0] / c.WINDOW_SCALE + offset[0] - 6, mpos[1] / c.WINDOW_SCALE + offset[1] - 6))

    def placement_point_is_valid(self):
        if not self.next_line_length():
            return False
        start = self.points_placed[-1]
        end = self.destination_position_scaled_level_space()
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        for i in range(21):
            through = i/20
            x = start[0] + dx*through
            y = start[1] + dy*through
            if (x < 0 or x > c.LEVEL_SIZE[0] - 1 or y < 0 or y > c.LEVEL_SIZE[1] - 1):
                return False
            if (self.level_surface.get_at((int(x), int(y))).b > 200):
                return False
        return True

    def placement_point_is_victory(self):
        if not self.next_line_length():
            return False
        if len(self.points_placed) < len(self.level_lines):
            return False
        if self.remaining_pickups():
            return False
        end = self.destination_position_scaled_level_space()
        dx = end[0] - self.destination_position[0]
        dy = end[1] - self.destination_position[1]
        if (dx**2 + dy**2 < self.destination_radius**2):
            return True
        return False

    def attempt_place_point(self):
        if self.won:
            return False
        if self.next_line_length() is None:
            return False
        if not self.placement_point_is_valid():
            self.game.shake(1)
            self.cant_place_sound.play()
            return False
        if (self.placement_point_is_victory()):
            self.won = True
        pickups_acquired = self.pickups_near_destination()
        self.pickups_per_move.append(pickups_acquired)
        if pickups_acquired:
            self.pickup_sound.play()
        self.points_placed.append(self.destination_position_scaled_level_space())
        self.game.shake(1)
        self.place_sound.play()
        return True

    def remaining_pickups(self):
        remaining_pickups = self.pickups.copy()
        for group in self.pickups_per_move:
            for pickup in group:
                if pickup in remaining_pickups:
                    remaining_pickups.remove(pickup)
        return remaining_pickups

    def pickups_near_destination(self):
        remaining_pickups = self.remaining_pickups()
        if not remaining_pickups:
            return []
        x, y = self.destination_position_scaled_level_space()
        result = []
        for x0, y0 in remaining_pickups:
            if (x - x0)**2 + (y - y0)**2 < self.pickup_radius**2:
                result.append((x0, y0))
        return result


    def draw_lines(self, surface, offset=(0, 0)):
        scale = 1
        longest_line = 1
        for line in self.level_lines:
            if line > longest_line:
                longest_line = line
        if longest_line > 80:
            scale = 80/longest_line
        x = 69
        y = 153
        dx = 5
        for i, line in [item for item in enumerate(self.level_lines)][::-1]:
            rect_surf = pygame.Surface((2, (int(line*scale))))

            if (i < len(self.points_placed) - 1):
                color = (42, 82, 114)
            elif i < len(self.points_placed):
                color = self.placement_line_color()
                if not self.show_placement_line():
                    x -= dx
                    continue
            else:
                color = (255, 255, 255)

            rect_surf.fill(color)
            surface.blit(rect_surf, (x + offset[0], y + offset[1] - rect_surf.get_height()))
            x -= dx

    def draw_points(self, surface, offset=(0, 0)):
        last_point = None
        for i, point in enumerate(self.points_placed):
            surf = None
            if i == 0:
                surf = self.start_point_surf
            else:
                surf = self.mid_point_surf
            x, y = point
            x += c.LEVEL_POSITION[0]
            y += c.LEVEL_POSITION[1]
            if surf is None:
                continue
            if last_point != None:
                x1 = last_point[0]
                y1 = last_point[1]
                pygame.draw.line(surface, (5, 27, 45, 128), (x + offset[0], y + offset[1] + 2),
                                 (x1 + offset[0], y1 + offset[1] + 2), width=2)
                pygame.draw.line(surface, (255, 255, 255), (x + offset[0], y + offset[1]), (x1 + offset[0], y1 + offset[1]), width=2)
            last_point = x, y
            surface.blit(surf, (x + offset[0] - surf.get_width()//2, y + offset[1] - surf.get_width()//2))

        if self.mouse_in_play_area() and last_point is not None and self.next_line_length() is not None:
            start = last_point
            mpos = self.cursor_position_scaled()
            dx = mpos[0] - start[0]
            dy = mpos[1] - start[1]
            if dx == 0:
                dx = 1 # avoid zero division
            line = Pose((dx, dy))
            line.scale_to(self.next_line_length())
            end = start[0] + int(line.x), start[1] + int(line.y)

            color = self.placement_line_color()

            pygame.draw.line(surface, (5, 27, 45), (start[0] + offset[0], start[1] + offset[1] + 1), (end[0] + offset[0], end[1] + offset[1] + 1), width=2)
            pygame.draw.line(surface, color, (start[0] + offset[0], start[1] + offset[1]), (end[0] + offset[0], end[1] + offset[1]), width=2)

            cursor = self.cursor_surf.copy()
            cursor_fill = cursor.copy()
            cursor_fill.fill(color)
            cursor.blit(cursor_fill, (0, 0), special_flags=pygame.BLEND_MULT)
            surface.blit(cursor,
                         (end[0] + offset[0] - 6, end[1] + offset[1] - 6))

    def show_placement_line(self):
        return time.time() % 0.5 < 0.25

    def placement_line_color(self):
        alpha = 0 if not self.show_placement_line() else 255
        if not self.placement_point_is_valid():
            return (255, 0, 0, alpha)
        if self.placement_point_is_victory() or self.pickups_near_destination():
            return (255, 255, 0, alpha)
        return (0, 255, 0, alpha)


