import pygame
import time
from timeit import default_timer as timer

import heapq
import math
import sys
import os
import psutil
from collections import deque
import csv

map_path ='pacman_map.csv'

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
PINK = (255, 192, 203)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

# Constants
CELL_SIZE = 30
WALL = 1
PATH = 0

class Maze:
    def __init__(self, layout):
        self.layout = layout
        self.height = len(layout)
        self.width = len(layout[0])

    def is_valid_position(self, position):
        x, y = position
        return (0 <= x < self.width and 
                0 <= y < self.height and 
                self.layout[y][x] == PATH)

    def get_neighbors(self, position):
        x, y = position
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_x, next_y = x + dx, y + dy
            if self.is_valid_position((next_x, next_y)):
                neighbors.append((next_x, next_y))
        return neighbors


class Character:
    def __init__(self, position):
        self.position = position
        self.previous_position = position


class PacMan(Character):
    def __init__(self, position):
        super().__init__(position)

    def move(self, direction, maze):
        dx, dy = direction
        new_position = (self.position[0] + dx, self.position[1] + dy)
        if maze.is_valid_position(new_position):
            self.previous_position = self.position
            self.position = new_position
            return True
        return False


class Ghost(Character):
    def __init__(self, position, color, name):
        super().__init__(position)
        self.color = color
        self.name = name
        self.path = []
        self.metrics = {
            "search_time": 0,
            "memory_usage": 0,
            "nodes_expanded": 0
        }
        self.last_target_position = None  # Track the last target position
    def find_path(self, maze, target_position):
        # 4 ghost classes will implement this method
        # This is a placeholder for the actual pathfinding algorithm
        pass

    def move(self, maze):
        if self.path:
            next_position = self.path.pop(0)
            if maze.is_valid_position(next_position):
                self.previous_position = self.position
                self.position = next_position
                return True
        return False

    def update_path(self, maze, target_position):
        if target_position != self.last_target_position:
            self.last_target_position = target_position
            self.find_path(maze, target_position)


class BlueGhost(Ghost):
    def __init__(self, position):
        super().__init__(position, BLUE, "Blue (BFS)")

    def find_path(self, maze, target_position):

        start_time = timer()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # BFS implementation
        queue = deque([(self.position, [])])  # (position, path)
        visited = {self.position}
        nodes_expanded = 0

        while queue:
            current_pos, path = queue.popleft()
            nodes_expanded += 1

            if current_pos == target_position:
                self.path = path
                break

            for next_pos in maze.get_neighbors(current_pos):
                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))

        search_time = timer() - start_time
        memory_used = process.memory_info().rss - memory_before

        self.metrics = {
            "search_time": search_time,
            "memory_usage": memory_used,
            "nodes_expanded": nodes_expanded
        }
        return self.metrics


class PinkGhost(Ghost):
    def __init__(self, position):
        super().__init__(position, PINK, "Pink (DFS)")

    def find_path(self, maze, target_position):
        start_time = timer()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # DFS implementation
        stack = [(self.position, [])]  # (position, path)
        visited = {self.position}
        nodes_expanded = 0

        while stack:
            current_pos, path = stack.pop()
            nodes_expanded += 1

            if current_pos == target_position:
                self.path = path
                break

            for next_pos in reversed(maze.get_neighbors(current_pos)):  # reversed để thứ tự gần giống BFS
                if next_pos not in visited:
                    visited.add(next_pos)
                    stack.append((next_pos, path + [next_pos]))

        search_time = timer() - start_time
        memory_used = process.memory_info().rss - memory_before

        self.metrics = {
            "search_time": search_time,
            "memory_usage": memory_used,
            "nodes_expanded": nodes_expanded
        }
        return self.metrics



class OrangeGhost(Ghost):
    def __init__(self, position):
        super().__init__(position, ORANGE, "Orange (UCS)")

    def find_path(self, maze, target_position):
        start_time = timer()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # UCS implementation
        frontier = []
        heapq.heappush(frontier, (0, self.position, []))  # (cost, position, path)
        visited = set()
        nodes_expanded = 0

        while frontier:
            cost, current_pos, path = heapq.heappop(frontier)
            nodes_expanded += 1

            if current_pos == target_position:
                self.path = path
                break

            if current_pos in visited:
                continue
            visited.add(current_pos)

            for neighbor in maze.get_neighbors(current_pos):
                if neighbor not in visited:
                    new_cost = cost + 1
                    heapq.heappush(frontier, (new_cost, neighbor, path + [neighbor]))

        search_time = timer() - start_time
        memory_used = process.memory_info().rss - memory_before

        self.metrics = {
            "search_time": search_time,
            "memory_usage": memory_used,
            "nodes_expanded": nodes_expanded
        }
        return self.metrics


class RedGhost(Ghost):
    def __init__(self, position):
        super().__init__(position, RED, "Red (A*)")

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, maze, target_position):
        start_time = time.time()
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        open_list = []
        heapq.heappush(open_list, (0, self.position, []))
        came_from = {}
        g_score = {self.position: 0}
        f_score = {self.position: self.heuristic(self.position, target_position)}
        visited = set()
        nodes_expanded = 0

        while open_list:
            _, current_pos, path = heapq.heappop(open_list)
            nodes_expanded += 1

            if current_pos in visited:
                continue

            visited.add(current_pos)

            if current_pos == target_position:
                self.path = path
                break

            for neighbor in maze.get_neighbors(current_pos):
                tentative_g_score = g_score[current_pos] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current_pos
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, target_position)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor, path + [neighbor]))

        search_time = time.time() - start_time
        memory_used = process.memory_info().rss - memory_before

        self.metrics = {
            "search_time": search_time,
            "memory_usage": memory_used,
            "nodes_expanded": nodes_expanded
        }
        return self.metrics


class Game:
    def __init__(self, maze_layout, user_controlled=True):
        self.maze = Maze(maze_layout)
        self.screen_width = self.maze.width * CELL_SIZE
        self.screen_height = self.maze.height * CELL_SIZE + 100  # Extra space for metrics
        self.pacman = PacMan((1, self.maze.height - 2))
        self.ghosts = [
            BlueGhost((self.maze.width - 2, 4)),
            PinkGhost((self.maze.width - 2, 3)),
            OrangeGhost((self.maze.width - 2, 2)),
            RedGhost((self.maze.width - 2, 1))
        ]
        self.user_controlled = user_controlled
        self.ghost_move = False
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.font = None
        self.big_font = None
        self.title_font = None
        self.level = 1
        self.parallel_execution = False
        self.pacman_move_counter = 0
        self.ghost_move_counter = 0
        self.pacman_speed = 5  # Pac-Man moves every 10 frame
        self.ghost_speed = 10  # Ghosts move every 30 frames
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Pac-Man Search Algorithms")
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.font = pygame.font.SysFont("Arial", 10)
        self.big_font = pygame.font.SysFont("Arial", 20)
        self.title_font = pygame.font.SysFont("Arial", 36)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_1:
                    self.level = 1
                    self.parallel_execution = False
                    self.user_controlled = True
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_2:
                    self.level = 2
                    self.parallel_execution = False
                    self.user_controlled = True
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_3:
                    self.level = 3
                    self.parallel_execution = False
                    self.user_controlled = True
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_4:
                    self.level = 4
                    self.parallel_execution = False
                    self.user_controlled = True
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_5:
                    self.level = 5
                    self.parallel_execution = True
                    self.user_controlled = True
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_6:
                    self.level = 6
                    self.parallel_execution = True
                    self.user_controlled = False
                    self.ghost_move = False
                    self.reset_game()
                elif event.key == pygame.K_RETURN:
                    self.user_controlled = not self.user_controlled
                    self.ghost_move = not self.ghost_move


    def update(self):
        if self.game_over:
            return
 
        # Increment movement counters
        self.pacman_move_counter += 1
        self.ghost_move_counter += 1

        # Check if any ghost caught Pac-Man
        for ghost in self.ghosts:
            if ghost.position == self.pacman.position:
                self.game_over = True
                return

        # Move Pac-Man every frame
        if self.pacman_move_counter >= self.pacman_speed:
            self.pacman_move_counter = 0
            # User control for PacMan
            if self.user_controlled and not self.game_over:
                keys = pygame.key.get_pressed()
                move_made = False
                
                if keys[pygame.K_UP]:
                    move_made = self.pacman.move((0, -1), self.maze)
                elif keys[pygame.K_DOWN]:
                    move_made = self.pacman.move((0, 1), self.maze)
                elif keys[pygame.K_LEFT]:
                    move_made = self.pacman.move((-1, 0), self.maze)
                elif keys[pygame.K_RIGHT]:
                    move_made = self.pacman.move((1, 0), self.maze)
                
            if self.user_controlled:
                for ghost in self.ghosts:
                    ghost.update_path(self.maze, self.pacman.position)




        # Move ghosts 
        if self.ghost_move_counter >= self.ghost_speed and self.ghost_move:
            self.ghost_move_counter = 0          

            if self.level == 1:
                active_ghost = self.ghosts[0]  # Blue Ghost
                active_ghost.update_path(self.maze, self.pacman.position)
                active_ghost.move(self.maze)
            elif self.level == 2:
                active_ghost = self.ghosts[1]  # Pink Ghost
                active_ghost.update_path(self.maze, self.pacman.position)
                active_ghost.move(self.maze)
            elif self.level == 3:
                active_ghost = self.ghosts[2]  # Orange Ghost
                active_ghost.update_path(self.maze, self.pacman.position)
                active_ghost.move(self.maze)
            elif self.level == 4:
                active_ghost = self.ghosts[3]  # Red Ghost
                active_ghost.update_path(self.maze, self.pacman.position)
                active_ghost.move(self.maze)
            elif self.level >= 5:  # Parallel execution for levels 5 and 6
                # Update paths for all ghosts if not user-controlled
                for ghost in self.ghosts:
                    ghost.update_path(self.maze, self.pacman.position)

                # Move all ghosts
                for i, ghost in enumerate(self.ghosts):
                    old_position = ghost.position
                    ghost.move(self.maze)

                    # Check for collisions with other ghosts
                    for j, other_ghost in enumerate(self.ghosts):
                        if i != j and ghost.position == other_ghost.position:
                            ghost.position = ghost.previous_position  # Revert move if collision
                            ghost.path.insert(0,ghost.previous_position)  # Add old position back to path
    def draw_maze(self):
        self.screen.fill(BLACK)
        
        # Draw maze
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.maze.layout[y][x] == WALL:
                    pygame.draw.rect(self.screen, BLUE, rect)
                else:
                    pygame.draw.rect(self.screen, BLACK, rect)
                    # Draw grid lines
                    pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw_characters(self):
        # Draw PacMan
        center_x = self.pacman.position[0] * CELL_SIZE + CELL_SIZE // 2
        center_y = self.pacman.position[1] * CELL_SIZE + CELL_SIZE // 2
        radius = CELL_SIZE // 2 - 2
        pygame.draw.circle(self.screen, YELLOW, (center_x, center_y), radius)
        
        # Draw active ghosts based on level
        if self.level == 1:
            self.draw_ghost(self.ghosts[0])
        elif self.level == 2:
            self.draw_ghost(self.ghosts[1])
        elif self.level == 3:
            self.draw_ghost(self.ghosts[2])
        elif self.level == 4:
            self.draw_ghost(self.ghosts[3])
        elif self.level >= 5:  # All ghosts for levels 5 and 6
            for ghost in self.ghosts:
                self.draw_ghost(ghost)

    def draw_ghost(self, ghost):
        x = ghost.position[0] * CELL_SIZE + CELL_SIZE // 4
        y = ghost.position[1] * CELL_SIZE + CELL_SIZE // 4
        width = CELL_SIZE // 2
        height = CELL_SIZE // 2
        pygame.draw.rect(self.screen, ghost.color, (x, y, width, height))
        
        # Draw path for debugging
        if ghost.path:
            for pos in ghost.path:
                center_x = pos[0] * CELL_SIZE + CELL_SIZE // 2
                center_y = pos[1] * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(self.screen, ghost.color, (center_x, center_y), 3)

    def draw_metrics(self):
        y_offset = self.maze.height * CELL_SIZE + 10
        
        # Draw level info
        level_text = f"Level {self.level}: "
        if self.level == 1:
            level_text += "Blue Ghost (BFS)"
            active_ghost = self.ghosts[0]
        elif self.level == 2:
            level_text += "Pink Ghost (DFS)"
            active_ghost = self.ghosts[1]
        elif self.level == 3:
            level_text += "Orange Ghost (UCS)"
            active_ghost = self.ghosts[2]
        elif self.level == 4:
            level_text += "Red Ghost (A*)"
            active_ghost = self.ghosts[3]
        elif self.level == 5:
            level_text += "All Ghosts (Parallel)"
            active_ghost = None
        elif self.level == 6:
            level_text += "User Control"
            active_ghost = None
        
        level_surface = self.big_font.render(level_text, True, WHITE)
        self.screen.blit(level_surface, (10, y_offset))
        
        # Draw metrics for appropriate ghost(s)
        if self.level <= 4:
            metrics_text = (
                f"Search Time: {active_ghost.metrics['search_time']:.7f} sec | "
                f"Memory: {active_ghost.metrics['memory_usage'] / 1024:.6f} KB | "
                f"Nodes: {active_ghost.metrics['nodes_expanded']}"
            )
            metrics_surface = self.font.render(metrics_text, True, WHITE)
            self.screen.blit(metrics_surface, (10, y_offset + 30))
        elif self.level >= 5:
            for i, ghost in enumerate(self.ghosts):
                metrics_text = (
                    f"{ghost.name}: Time: {ghost.metrics['search_time']:.7f} sec | "
                    f"Memory: {ghost.metrics['memory_usage'] / 1024:.2f} KB | "
                    f"Nodes: {ghost.metrics['nodes_expanded']}"
                    f"Position: {ghost.position}"
                )
                metrics_surface = self.font.render(metrics_text, True, ghost.color)
                self.screen.blit(metrics_surface, (10, y_offset + 30 + i * 15))

        # Draw controls info
        controls_text = "Controls: 1-6 - Change Level | Enter - Start/Pause | R - Reset | ESC - Quit | Arrow Keys - Move Pac-Man (Level 6)"
        controls_surface = self.font.render(controls_text, True, GREEN)
        self.screen.blit(controls_surface, (10, y_offset + 70))

    def draw_game_over(self):
        if self.game_over:
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            for i, ghost in enumerate(self.ghosts):
                metrics_text = (
                    f"{ghost.name}: Time: {ghost.metrics['search_time']:.6f} sec | "
                    f"Memory: {ghost.metrics['memory_usage'] / 1024:.2f} KB | "
                    f"Nodes: {ghost.metrics['nodes_expanded']}"
                )
                metrics_surface = self.big_font.render(metrics_text, True, ghost.color)
                metrics_rec = metrics_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 40))
                self.screen.blit(metrics_surface, (metrics_rec.x, metrics_rec.y + i * 20))
                
            #result_text = self.title_font.render("GAME OVER", True, RED)
            #text_rect = result_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 20))
            #self.screen.blit(result_text, text_rect)
            
            restart_text = self.big_font.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 40))
            self.screen.blit(restart_text, restart_rect)

    def draw(self):
        self.draw_maze()
        self.draw_characters()
        self.draw_metrics()
        self.draw_game_over()
        pygame.display.flip()

    def reset_game(self):
        self.pacman.position = (1, self.maze.height - 2)
        self.ghosts[0].position = (self.maze.width - 2, 4)  # Blue
        self.ghosts[1].position = (self.maze.width - 2, 3)  # Pink
        self.ghosts[2].position = (self.maze.width - 2, 2)  # Orange
        self.ghosts[3].position = (self.maze.width - 2, 1)  # Red
        for ghost in self.ghosts:
            ghost.last_target_position = None  # Reset last target position
        
        for ghost in self.ghosts:
            ghost.path = []
        
        self.game_over = False

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)  # FPS 

        pygame.quit()
        sys.exit()


def create_maze_layout(width, height):
    """Create a simple maze layout with walls around the edges and some internal walls"""
    layout = [[PATH for _ in range(width)] for _ in range(height)]

    with open(map_path, 'r') as file:
        reader = csv.reader(file)
        for y, row in enumerate(reader):
            for x, cell in enumerate(row):
                if cell == '1':
                    layout[y][x] = WALL
                else:
                    layout[y][x] = PATH
    
    return layout


def main():
    # Create a maze layout
    maze_layout = create_maze_layout(32, 28)
    
    # Create and run the game
    game = Game(maze_layout)
    game.run()


if __name__ == "__main__":
    main()