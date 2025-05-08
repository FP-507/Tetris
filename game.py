import pygame
import random
import os
import sys

# Inicializar pygame
pygame.init()
pygame.mixer.init()

# =============================================================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================================================

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)

# Configuración del juego
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 8)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT
GAME_AREA_LEFT = BLOCK_SIZE

# Formas de las piezas
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # J
    [[1, 1, 1], [0, 0, 1]],  # L
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

COLORS = [CYAN, YELLOW, PURPLE, BLUE, ORANGE, GREEN, RED]

# =============================================================================
# CLASE DEL JUEGO TETRIS CON MEJORAS
# =============================================================================

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Tetris Mejorado')
        self.clock = pygame.time.Clock()
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.paused = False
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        self.lines_cleared = 0
        self.lines_to_next_level = 5
        self.fall_speed = 0.5  # segundos
        self.font = pygame.font.SysFont('Arial', 25)
        self.big_font = pygame.font.SysFont('Arial', 40, bold=True)
        
        # Cargar sonidos (si no existen, se usará sonido silencioso)
        self.sound_clear = self.load_sound('clear.wav')
        self.sound_drop = self.load_sound('drop.wav')
        self.sound_rotate = self.load_sound('rotate.wav')
        self.sound_gameover = self.load_sound('gameover.wav')
    
    def load_sound(self, filename):
        """Intenta cargar un sonido, devuelve un sonido silencioso si falla."""
        try:
            return pygame.mixer.Sound(os.path.join('sounds', filename))
        except:
            # Crear un sonido silencioso como fallback
            silent_sound = pygame.mixer.Sound(buffer=bytes(44))
            return silent_sound
    
    def load_high_score(self):
        """Carga el high score desde un archivo, o devuelve 0 si no existe."""
        try:
            with open('highscore.txt', 'r') as f:
                return int(f.read())
        except:
            return 0
    
    def save_high_score(self):
        """Guarda el high score en un archivo."""
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open('highscore.txt', 'w') as f:
                    f.write(str(self.high_score))
            except:
                pass
    
    def new_piece(self):
        """Crea una nueva pieza aleatoria."""
        shape = random.choice(SHAPES)
        color = COLORS[SHAPES.index(shape)]
        x = GRID_WIDTH // 2 - len(shape[0]) // 2
        y = 0
        return {'shape': shape, 'color': color, 'x': x, 'y': y}
    
    def valid_move(self, piece, x_offset=0, y_offset=0):
        """Verifica si un movimiento es válido."""
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + x_offset
                    new_y = piece['y'] + y + y_offset
                    if (new_x < 0 or new_x >= GRID_WIDTH or 
                        new_y >= GRID_HEIGHT or 
                        (new_y >= 0 and self.grid[new_y][new_x])):
                        return False
        return True
    
    def rotate_piece(self):
        """Rota la pieza actual si es posible."""
        old_shape = self.current_piece['shape']
        rotated = [list(row)[::-1] for row in zip(*self.current_piece['shape'])]
        self.current_piece['shape'] = rotated
        if not self.valid_move(self.current_piece):
            self.current_piece['shape'] = old_shape
        else:
            self.sound_rotate.play()
    
    def lock_piece(self):
        """Fija la pieza en el tablero y verifica líneas completas."""
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    if self.current_piece['y'] + y < 0:
                        self.game_over = True
                        self.sound_gameover.play()
                    else:
                        self.grid[self.current_piece['y'] + y][self.current_piece['x'] + x] = self.current_piece['color']
        
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        self.sound_drop.play()
    
    def clear_lines(self):
        """Elimina líneas completas y actualiza puntuación y nivel."""
        lines_cleared = 0
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_cleared += 1
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2-1][:]
                self.grid[0] = [0 for _ in range(GRID_WIDTH)]
        
        if lines_cleared > 0:
            self.sound_clear.play()
            self.lines_cleared += lines_cleared
            
            # Actualizar puntuación según líneas completadas
            score_values = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += score_values.get(lines_cleared, 0) * self.level
            
            # Actualizar nivel
            self.lines_to_next_level -= lines_cleared
            if self.lines_to_next_level <= 0:
                self.level += 1
                self.lines_to_next_level = 5
                self.fall_speed = max(0.05, self.fall_speed * 0.75)  # Aumenta velocidad
    
    def draw_grid(self):
        """Dibuja el tablero y los bloques colocados."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen, 
                    WHITE, 
                    (GAME_AREA_LEFT + x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 
                    1
                )
                if self.grid[y][x]:
                    pygame.draw.rect(
                        self.screen, 
                        self.grid[y][x], 
                        (GAME_AREA_LEFT + x * BLOCK_SIZE + 1, y * BLOCK_SIZE + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
                    )
    
    def draw_piece(self, piece):
        """Dibuja la pieza actual."""
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen, 
                        piece['color'], 
                        (GAME_AREA_LEFT + (piece['x'] + x) * BLOCK_SIZE + 1, 
                         (piece['y'] + y) * BLOCK_SIZE + 1, 
                         BLOCK_SIZE - 2, BLOCK_SIZE - 2)
                    )
    
    def draw_sidebar(self):
        """Dibuja la barra lateral con información del juego."""
        sidebar_x = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 20
        
        # Siguiente pieza
        next_text = self.font.render("Siguiente:", True, WHITE)
        self.screen.blit(next_text, (sidebar_x, 30))
        
        for y, row in enumerate(self.next_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen, 
                        self.next_piece['color'], 
                        (sidebar_x + 10 + x * BLOCK_SIZE, 
                         80 + y * BLOCK_SIZE, 
                         BLOCK_SIZE - 2, BLOCK_SIZE - 2)
                    )
        
        # Puntuación
        score_text = self.font.render(f"Puntos: {self.score}", True, WHITE)
        self.screen.blit(score_text, (sidebar_x, 180))
        
        # High Score
        high_text = self.font.render(f"Récord: {self.high_score}", True, WHITE)
        self.screen.blit(high_text, (sidebar_x, 220))
        
        # Nivel
        level_text = self.font.render(f"Nivel: {self.level}", True, WHITE)
        self.screen.blit(level_text, (sidebar_x, 260))
        
        # Líneas
        lines_text = self.font.render(f"Líneas: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (sidebar_x, 300))
        
        # Controles
        controls = [
            "Controles:",
            "← → : Mover",
            "↑ : Rotar",
            "↓ : Bajar",
            "Espacio: Caída",
            "P : Pausa"
        ]
        
        for i, line in enumerate(controls):
            control_text = self.font.render(line, True, WHITE)
            self.screen.blit(control_text, (sidebar_x, 360 + i * 30))
    
    def draw_game_over(self):
        """Dibuja la pantalla de Game Over."""
        if self.game_over:
            # Fondo semitransparente
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Texto de Game Over
            game_over_text = self.big_font.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(game_over_text, text_rect)
            
            # Puntuación final
            score_text = self.font.render(f"Puntuación final: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
            self.screen.blit(score_text, score_rect)
            
            # Instrucciones para reiniciar
            restart_text = self.font.render("Presiona R para reiniciar", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            self.screen.blit(restart_text, restart_rect)
    
    def draw_pause(self):
        """Dibuja la pantalla de pausa."""
        if self.paused:
            # Fondo semitransparente
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Texto de Pausa
            pause_text = self.big_font.render("PAUSA", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
    
    def reset_game(self):
        """Reinicia el juego."""
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.lines_to_next_level = 5
        self.fall_speed = 0.5
        self.save_high_score()
    
    def run(self):
        """Bucle principal del juego."""
        fall_time = 0
        last_time = pygame.time.get_ticks()
        
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000
            last_time = current_time
            
            # Lógica del juego (solo si no está pausado o en game over)
            if not self.game_over and not self.paused:
                fall_time += delta_time
                if fall_time >= self.fall_speed:
                    fall_time = 0
                    if self.valid_move(self.current_piece, 0, 1):
                        self.current_piece['y'] += 1
                    else:
                        self.lock_piece()
            
            # Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.save_high_score()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset_game()
                    
                    if event.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused
                    
                    if not self.game_over and not self.paused:
                        if event.key == pygame.K_LEFT and self.valid_move(self.current_piece, -1, 0):
                            self.current_piece['x'] -= 1
                        elif event.key == pygame.K_RIGHT and self.valid_move(self.current_piece, 1, 0):
                            self.current_piece['x'] += 1
                        elif event.key == pygame.K_DOWN and self.valid_move(self.current_piece, 0, 1):
                            self.current_piece['y'] += 1
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            while self.valid_move(self.current_piece, 0, 1):
                                self.current_piece['y'] += 1
                            self.lock_piece()
            
            # Renderizado
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_piece(self.current_piece)
            self.draw_sidebar()
            self.draw_game_over()
            self.draw_pause()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# =============================================================================
# EJECUCIÓN DEL JUEGO
# =============================================================================

if __name__ == "__main__":
    # Crear directorio de sonidos si no existe
    if not os.path.exists('sounds'):
        os.makedirs('sounds')
        print("Crea archivos de sonido en la carpeta 'sounds' para mejor experiencia")
    
    game = Tetris()
    game.run()