"""
This is where the implementation of the plugin code goes.
The auto-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('auto')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class auto(PluginBase):
  def main(self):
    active_node = self.active_node
    core = self.core
    logger = self.logger
    self.namespace = None
    META = self.META
    logger.debug('path: {0}'.format(core.get_path(active_node)))
    logger.info('name: {0}'.format(core.get_attribute(active_node, 'name')))
    logger.warn('pos : {0}'.format(core.get_registry(active_node, 'position')))
    logger.error('guid: {0}'.format(core.get_guid(active_node)))
    
    currentGameStatePath = core.get_pointer_path(active_node,'currentGameState')
    self.currentGameState = core.load_by_path(self.root_node,currentGameStatePath)
    
    nodesList = core.load_sub_tree(active_node)
    nodes = {}
    for node in nodesList:
      nodes[core.get_path(node)] = node
    self.nodes = nodes
      


    states = []
    for path in nodes:
      node = nodes[path]
      name = core.get_attribute(node, 'name')
      if (core.is_instance_of(node, META['GameState'])):
        currentMove= nodes[core.get_pointer_path(node, "currentMove")]
        currentMoveColor = core.get_attribute(currentMove,'color')
        currentMoveTile = core.get_parent(currentMove)
        currentMoveTileRow = core.get_attribute(currentMoveTile, 'row')
        currentMoveTileColumn = core.get_attribute(currentMoveTile, 'column')
        currentPlayer = core.get_attribute(nodes[core.get_pointer_path(node, "currentPlayer")], 'name')
        states.append({"path": path, "name": name, "board": [[None for x in range(8)] for x  in range(8)], "currentPlayer" : currentPlayer,
        "currentMoveColor": currentMoveColor, "currentMoveTileRow": currentMoveTileRow, "currentMoveTileColumn": currentMoveTileColumn}) 
      if (core.is_instance_of(node, META['Tile'])):
        #logger.warn(node)
        for state in states:
          if state["path"][:4] == path[:4]:
            row = core.get_attribute(node, 'row')
            column = core.get_attribute(node, 'column')
            children = core.get_children_paths(node)
            flips = []
            childColor = None
            childPath = None
            if len(children) > 0:
              childPath = children[0]
              childColor = core.get_attribute(nodes[childPath], 'color')
              for path2 in nodes:
                node2 = nodes[path2]
                if (core.is_instance_of(node2, META['mightFlip'])):
                  srcTile = core.get_parent(nodes[core.get_pointer_path(node2, 'src')])
                  dstTile = core.get_parent(nodes[core.get_pointer_path(node2, 'dst')])
                  srcInfo = {'column': core.get_attribute(srcTile, 'column'), 'row':core.get_attribute(srcTile,'row')}
                  dstInfo = {'column': core.get_attribute(dstTile, 'column'), 'row':core.get_attribute(dstTile,'row')}

                  if node == srcTile:
                    flips.append(dstInfo)
                  
            state["board"][row][column] = {"color": childColor, "flips": flips}
            
    self.states = states
    
    nodesList = core.load_sub_tree(active_node)
    nodes = {}
    for node in nodesList:
      nodes[core.get_path(node)] = node
      if (core.is_instance_of(node, META['GameState'])):
        logger.info(core.get_attribute(node, 'name'))
    self.nodes=nodes
#    self.counting_pieces()
#    self.Undo()
#   self.tile_highlight()
    self.auto()
      
      
  def counting_pieces(self):
      counter_black = 0
      counter_white = 0
      META = self.META
      core = self.core
      logger = self.logger
      current_node = self.active_node
      nodesList = core.load_sub_tree(current_node)
      nodes = {}
      for node in nodesList:
        nodes[core.get_path(node)] = node
      current_game_state_path = core.get_pointer_path(current_node,'currentGameState')
      current_game_state = nodes[current_game_state_path]
      children_paths = self.core.get_children_paths(current_game_state)
      piece_count = 0
      for path in children_paths:
        node = core.load_by_path(self.root_node, path)
        if self.core.is_instance_of(node,META['Board']):
          tile_paths = self.core.get_children_paths(node)
          for tile_path in tile_paths:
            tile_node = core.load_by_path(self.root_node, tile_path)
            if self.core.is_instance_of(tile_node,META['Tile']):
              piece_paths = self.core.get_children_paths(tile_node)
              if len(piece_paths) > 0:
                for piece_path in piece_paths:
                  piece_node = core.load_by_path(self.root_node, piece_path)
                  color = None
                  if self.core.is_instance_of(piece_node,META['Piece']):
                    color = core.get_attribute(piece_node, 'color')
                    piece_count += 1
                  if color == 'black':
                    counter_black += 1
                  elif color == 'white':
                    counter_white += 1
      logger.info('Black pieces: {0}'.format(counter_black))
      logger.info('White pieces: {0}'.format(counter_white))
      logger.info('Total pieces: {0}'.format(piece_count))
      
  def Undo(self):
      META = self.META
      core = self.core
      logger = self.logger
      self.namespace = None
        
      current_game_state_path = core.get_pointer_path(self.active_node,'currentGameState')
      current_state = core.load_by_path(self.root_node,current_game_state_path)
      previous_game_state_path = core.get_pointer_path(self.currentGameState, 'previousGameState')
      previous_state = core.load_by_path(self.root_node,previous_game_state_path)
      core.set_pointer(self.active_node, 'currentGameState',previous_state)
      core.delete_node(current_state)
      
      self.util.save(self.root_node, self.commit_hash, self.branch_name)
      
  def next_move_viable(self, tile):
    self.valid = False
    self.to_flip = []
    self.next_moves = {"black":"white", "white": "black"}
    flip_directions = [(0,1), (1,0), (1,1), (-1,-1), (1,-1), (-1,1), (-1,0), (0,-1)]
    logger = self.logger
    core = self.core
    current_node = self.active_node
    current_tile = tile
    current_tile_nodes = []
    self.current_tile_nodes=current_tile_nodes
 
    current_move_path = core.get_pointer_path(self.currentGameState, "currentMove")
    current_move = core.load_by_path(self.root_node,current_move_path)
    
    current_move_color = core.get_attribute(current_move, 'color')
    next_move_color = self.next_moves[current_move_color]
    self.next_move_color = next_move_color
    state_path = self.currentGameState["nodePath"]
    for state in self.states:
      if state_path == state['path']:
        board_ref = state['board']
        column = core.get_attribute(current_tile, 'column')
        row = core.get_attribute(current_tile, 'row')
        if board_ref[row][column]['color'] == None:
          for direction in flip_directions:
            to_flip = []
            rows = len(board_ref)
            columns = len(board_ref[0])
            new_row = row + direction[0]
            new_column = column + direction[1]
            if 0 <= new_row < rows and 0 <= new_column < columns and board_ref[new_row][new_column] is not None:
              if board_ref[row + direction[0]][column + direction[1]]['color'] == current_move_color:
                to_flip = [(row + direction[0], column + direction[1])]
                multiplier = 2
                while (row + (direction[0]*multiplier) > 0 and row + (direction[0]*multiplier) < 8) and (column + (direction[1]*multiplier) > 0 and column + (direction[1]*multiplier) < 8):
                  if board_ref[row + direction[0]*multiplier][column + (direction[1]*multiplier)]['color'] == next_move_color:
                    end_position = (row + direction[0]*multiplier, column + (direction[1]*multiplier))
                    for position in to_flip:
                      self.to_flip.append(position)
                    self.valid = True
                    self.current_tile_nodes.append(current_tile)
                  to_flip.append((row + direction[0]*multiplier, column + (direction[1]*multiplier)))
                  multiplier +=1
    return self.valid, self.current_tile_nodes, self.to_flip
  
  def tile_highlight(self):
    META = self.META
    core = self.core
    logger = self.logger
    game_folder=self.active_node

    current_node = self.currentGameState
    correct_tile_nodes = []
    correct_tiles = []
    correct_flip = []
    children_paths = core.get_children_paths(current_node)
    for child_path in children_paths:
      child=core.load_by_path(self.root_node,child_path)
      if core.is_instance_of(child, META["Board"]):
        board = child
        tile_paths = core.get_children_paths(board)
        for tile_path in tile_paths:
          
          tile = core.load_by_path(self.root_node, tile_path)
          if core.is_instance_of(tile,META["Tile"]):
            valid,current_tiles,flip=self.next_move_viable(tile)          
            if(valid==True):
              correct_tile_nodes.append(tile)
              correct_flip.append(flip)
    for i in correct_tile_nodes:
      correct_tiles.append([core.get_attribute(i,'row'),core.get_attribute(i,'column')])
    logger.info(correct_tiles)
    return correct_tile_nodes,correct_flip
    
  def auto_next_state(self,auto_tile,auto_flip):
    import re
    active_node = self.active_node
    core = self.core
    logger = self.logger
    META = self.META
    nodes = self.nodes
    self.row = core.get_attribute(auto_tile, 'row')
    self.column = core.get_attribute(auto_tile, 'column')
    parent_name = core.get_attribute(self.currentGameState, 'name')
    new_name = parent_name + "_1"
    try:
      for i, c in enumerate(parent_name):
        if c.isdigit():
          number_index = i
          break
      state_number = int(parent_name[number_index:]) + 1
      new_name = parent_name[:number_index] + f"{state_number}"
    except:
      pass
    copied_node = core.copy_node(self.currentGameState,active_node)
    core.set_attribute(copied_node, 'name', new_name)
    core.set_pointer(copied_node,'previousGameState',self.currentGameState)
    core.set_pointer(active_node,'currentGameState',copied_node)
    child_paths=core.get_children_paths(copied_node)
    old_player = core.get_pointer_path(copied_node, "currentPlayer")
    for child_path in child_paths:
      child = core.load_by_path(self.root_node, child_path)
      if core.is_instance_of(child, META["Player"]):
        if not child_path == old_player:
          core.set_pointer(copied_node, "currentPlayer", child)
      if core.is_instance_of(child, META["Board"]):
        board = child
        tile_paths = core.get_children_paths(board)
        for tile_path in tile_paths:
          tile = core.load_by_path(self.root_node, tile_path)
          if core.get_attribute(tile, 'row') ==self.row and core.get_attribute(tile, 'column') ==self.column:
            created_piece = core.create_node({'parent':tile, 'base': META["Piece"]})
            core.set_pointer(copied_node, "currentMove", created_piece)
            core.set_attribute(created_piece, 'color', self.next_move_color)
          elif (core.get_attribute(tile, 'row'), core.get_attribute(tile, 'column')) in auto_flip:
            piece_path = core.get_children_paths(tile)[0]
            core.set_attribute(core.load_by_path(self.root_node, piece_path), 'color', self.next_move_color)
    
    self.util.save(self.root_node, self.commit_hash, self.branch_name)
    
  def auto(self):
    from random import randrange
    active_node = self.active_node
    core = self.core
    logger = self.logger
    META = self.META
    tiles,flips = self.tile_highlight()
    rand_ind = randrange(len(tiles))
    self.auto_next_state(tiles[rand_ind],flips[rand_ind])