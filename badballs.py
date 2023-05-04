#!/usr/bin/env python
# Hoesel Markus

SCREEN_SIZE = ( 640, 480 )
BALL_COUNT = 2 

import pygame
from pygame.locals import *

from random import randint, choice
from vector2 import Vector2

class State( object ):

	def __init__( self, name ):
		self.name = name

	def do_actions( self ):
		pass

	def check_conditions( self ):
		pass

	def entry_actions( self ):
		pass

	def exit_actions( self ):
		pass

class StateMachine( object ):

	def __init__( self ):

		self.states = { }
		self.active_state = None

	def add_state( self, state ):
		self.states[ state.name ] = state

	def think( self ):

		if self.active_state is None:
			return

		self.active_state.do_actions( )

		new_state_name = self.active_state.check_conditions( )
		if new_state_name is not None:
			self.set_state( new_state_name )

	def set_state( self, new_state_name ):

		if self.active_state is not None:
			self.active_state.exit_actions( )

		self.active_state = self.states[ new_state_name ]
		self.active_state.entry_actions( )

class World( object ):

	def __init__( self ):

		self.entities = { }
		self.entity_id = 0

		background_image_filename = 'galaxy.jpg'
		self.background = pygame.image.load( \
		 background_image_filename ).convert( )

	def add_entity( self, entity ):

		self.entities[ self.entity_id ] = entity
		entity.id = self.entity_id
		self.entity_id += 1

	def remove_entity( self, entity ):

		del self.entities[ entity.id ]

	def get( self, entity_id ):

		if entity_id in self.entities:
			return self.entities[ entity_id ]
		else:
			return None

	def process( self, time_passed ):

		time_passed_seconds = time_passed / 1000.0

		for entity in self.entities.values( ):
			entity.process( time_passed_seconds )

	def render( self, surface ):

		surface.blit( self.background, ( 0, 0 ) )

		for entity in self.entities.itervalues( ):
			entity.render( surface )

	def get_close_entity( self, name, location, range = 100. ):

		location = Vector2( *location )

		for entity in self.entities.itervalues( ):
				if entity.name == name:
					distance = location.get_distance_to( \
					 entity.location )

					if distance < range:
						return entity
		return None

class GameEntity( object ):

	def __init__( self, world, name, image ):

		self.world = world
		self.name = name
		self.image = image
		self.location = Vector2( 0, 0 )
		self.destination = Vector2( 0, 0 )
		self.speed = 0.
		self.direction = 0

		self.brain = StateMachine( )

		self.id = 0

	def render( self, surface ):

		x, y = self.location
		w, h = self.image.get_size( )
		surface.blit( self.image, ( x - w / 2, y - h / 2 ) )

	def process( self, time_passed ):

		self.brain.think( )

		if self.speed > 0 and self.location != self.destination:

			vec_to_destination = self.destination - self.location
			distance_to_destination = vec_to_destination.get_length( )
			heading = vec_to_destination.get_normalized( )
			travel_distance = min( distance_to_destination, \
			 time_passed * self.speed )
			self.location += travel_distance * heading

		elif self.direction > 0:
			self.location += self.direction * time_passed * 170

class Point( GameEntity ):

	def __init__( self, world, image ):
		GameEntity.__init__( self, world, "point", image )



class Player( GameEntity ):

	def __init__( self, world, image ):

		self.point_counter = 0
		self.level_counter = 0
		self.help_counter = 0
		GameEntity.__init__( self, world, "player", image )
		self.dead_image = pygame.transform.flip( image, 0, 1 )
		self.health = 1
		self.point_image = pygame.image.load( "bug.png" ).convert_alpha( )
		self.w, self.h = SCREEN_SIZE

	def bitten( self ):

		self.health -= 1
		if self.health <= 0:
			self.speed = 0.
			self.direction = 0
			self.image = self.dead_image

	def render( self, surface ):

		GameEntity.render( self, surface )

	def process( self, time_passed ):

		point = self.world.get_close_entity( "point",  self.location, 25. )

		if point is not None:
			self.point_id = point.id
			self.world.remove_entity( point )
			self.point_counter += 1
			point = Point( self.world, self.point_image )
			point.location = Vector2( randint( 0, self.w ), randint( 0, self.h ) )
			self.world.add_entity( point )

		GameEntity.process( self, time_passed )


class Ball( GameEntity ):

	def __init__( self, world, image ):

		GameEntity.__init__( self, world, "ball", image )

		lazy_state = BallStateLazy( self )
		hunting_state = BallStateHunting( self )

		self.brain.add_state( lazy_state )
		self.brain.add_state( hunting_state )

	def render( self, surface ):

		GameEntity.render( self, surface )

class BallStateLazy( State ):

	def __init__( self, ball ):
		State.__init__( self, "lazy" )
		self.ball = ball
		self.player_id = None
		self.location = self.random_location( )

	def random_location( self ):
		w, h = SCREEN_SIZE
		self.ball.location = Vector2( randint( 0, w ), randint( 0, h ) )

	def random_destination( self ):
		w, h = SCREEN_SIZE
		self.ball.destination = Vector2( randint( 0, w ), randint( 0, h ) )

	def do_actions( self ):
		if randint(1, 100 ) == 1:
			self.random_destination( )

	def check_conditions( self ):

		player = self.ball.world.get_close_entity( \
		 "player", self.ball.location, 200. )
		if player is not None:
			self.ball.player_id = player.id
			return "hunting"

		return None

	def entry_actions( self ):
		self.ball.speed = 30. +randint( -20, 20 )
		self.random_destination( )

class BallStateHunting( State ):

	def __init__( self, ball ):
		State.__init__( self, "hunting" )
		self.ball = ball
		self.got_kill = False

	def do_actions( self ):

		player = self.ball.world.get( self.ball.player_id )

		if player is None:
			return

		self.ball.destination = player.location

		if self.ball.location.get_distance_to( player.location) < 30.:

			player.bitten( )

			if player.health <= 0:
				self.ball.world.remove_entity( player )
				self.got_kill = True

	def check_conditions( self ):

		player = self.ball.world.get( self.ball.player_id )

		if self.got_kill:
			return "lazy"

		if player is not None:
			if self.ball.location.get_distance_to( \
			 player.location ) > 210.:
				self.ball.player_id = player.id
				return "lazy"
		return None

	def entry_actions( self ):

		self.ball.speed = 30. + randint( -20, +20 )

	def exit_actions( self ):
		self.got_kill = False

def run( ):

	pygame.init( )
	screen = pygame.display.set_mode( SCREEN_SIZE, 0, 32 )

	world = World( )

	w, h = SCREEN_SIZE

	clock = pygame.time.Clock( )

	ball_image = pygame.image.load( "alien.png" ).convert_alpha( )
	player_image = pygame.image.load( "ufo.png" ).convert_alpha( )
	point_image = pygame.image.load( "bug.png" ).convert_alpha( )

	for ball_no in xrange( BALL_COUNT ):
		ball = Ball( world, ball_image )
		ball.brain.set_state( "lazy" )
		world.add_entity( ball )

	player = Player( world, player_image )
	player.location = Vector2( 50, 250 )
	world.add_entity( player )

	point = Point( world, point_image )
	point.location = Vector2( randint( 0, w ), randint( 0, h ) )
	world.add_entity( point )

	while True:

		for event in pygame.event.get( ):
			if event.type == QUIT:
				return

		time_passed = clock.tick( 30 )
		
		if player.point_counter == player.help_counter:
			player.help_counter += 10
			player.level_counter += 1
			ball = Ball( world, ball_image )
			ball.brain.set_state( "lazy" )
			world.add_entity( ball )

		world.process( time_passed )
		world.render( screen )

		pressed_keys = pygame.key.get_pressed( )

		key_direction = Vector2( 0, 0 )

		if pressed_keys[ K_LEFT ]:
			key_direction.x = -1
		elif pressed_keys[ K_RIGHT ]:
			key_direction.x = +1
		if pressed_keys[ K_UP ]:
			key_direction.y = -1
		elif pressed_keys[ K_DOWN ]:
			key_direction.y = +1
		if pressed_keys[ K_y ]:

			world = World( )

			w, h = SCREEN_SIZE

			clock = pygame.time.Clock( )

			ball_image = pygame.image.load( "alien.png" ).convert_alpha( )
			player_image = pygame.image.load( "ufo.png" ).convert_alpha( )
			point_image = pygame.image.load( "bug.png" ).convert_alpha( )

			for ball_no in xrange( BALL_COUNT ):
				ball = Ball( world, ball_image )
				ball.brain.set_state( "lazy" )
				world.add_entity( ball )

			player = Player( world, player_image )
			player.location = Vector2( 50, 250 )
			world.add_entity( player )

			point = Point( world, point_image )
			point.location = Vector2( randint( 0, w ), randint( 0, h ) )
			world.add_entity( point )


		key_direction.normalize( )

		player.direction = Vector2( key_direction.x, key_direction.y )

		font = pygame.font.SysFont( "impact", 20 );
		font_surface = font.render( "Points =" + str( player.point_counter ) \
		 + ", Level =" + str( player.level_counter ), True, ( 0, 255, 0) )
		screen.blit( font_surface, (10, 10 ) )	

		newgame = pygame.font.SysFont( "impact", 12 );
		newgame_surface = newgame.render( "Press \"Y\" for new game", True, ( 0, 0, 255 ) )
		screen.blit( newgame_surface, ( 10, 35 ) )

		pygame.display.update( )

if __name__ == "__main__":
	run( )
