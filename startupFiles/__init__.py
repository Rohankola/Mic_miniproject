"""
This is where the implementation of the plugin code goes.
The abc-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('abc')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class abc(PluginBase):
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
    
   
    nodesList = core.load_sub_tree(active_node)
    
    nodes = {}
    game_states=[]
    for node in nodesList:
      nodes[core.get_path(node)] = node
    self.nodes=nodes
    
    current_gs_path=core.get_pointer_path(active_node,'currentGameState')
    current_gs=nodes[current_gs_path]
    self.current_gs=current_gs
    #logger.info(core.get_attribute(current_gs,'name'))
    
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
    #logger.info(states)
    self.undo()
    #self.highlight_tile()
    #self.count_color()
#    self.auto()
    #self.make_new_state()
    
  def next_move_viable(self, tile):
    self.valid = False
    self.to_flip = []
    META = self.META
    self.next_moves = {"black":"white", "white": "black"}
    flip_directions = [(0,1), (1,0), (1,1), (-1,-1), (1,-1), (-1,1), (-1,0), (0,-1)]
    logger = self.logger
    core = self.core
    current_tile=tile
    current_tile_nodes=[]
    self.current_tile_nodes=current_tile_nodes
    
    current_move = self.nodes[core.get_pointer_path(self.current_gs, "currentMove")]
    current_move_color = core.get_attribute(current_move, 'color')
    next_move_color = self.next_moves[current_move_color]
    self.next_move_color = next_move_color
    state_path = self.current_gs["nodePath"]
    
    '''
    next_move_color = self.next_moves[current_move_color]
    self.next_move_color = next_move_color
   
    board_ref=states["board"]
    
    column = core.get_attribute(current_tile, 'column')
    row = core.get_attribute(current_tile, 'row')
    '''
    
    
    for state in self.states:
      if state_path == state['path']:
        board_ref = state['board']
        column = core.get_attribute(current_tile, 'column')
        row = core.get_attribute(current_tile, 'row')
        if board_ref[row][column]['color'] == None:
          for direction in flip_directions:
            to_flip = []
            rows = len(board_ref)      # Number of rows in the board
            columns = len(board_ref[0]) # Number of columns in the board (assuming all rows are of equal length)

        # Calculate new indices
            new_row = row + direction[0]
            new_column = column + direction[1]
            if 0 <= new_row < rows and 0 <= new_column < columns and board_ref[new_row][new_column] is not None:
              if board_ref[row + direction[0]][column + direction[1]]['color'] == current_move_color:
                to_flip = [(row + direction[0], column + direction[1])]
                multiplier = 2
                while (row + (direction[0]*multiplier) > 0 and row + (direction[0]*multiplier) < 8) and (column + (direction[1]*multiplier) > 0 and column + (direction[1]*multiplier) < 8) and board_ref[row + direction[0]*multiplier][column + (direction[1]*multiplier)]!=None:
                  if board_ref[row + direction[0]*multiplier][column + (direction[1]*multiplier)]['color'] == next_move_color:
                    end_position = (row + direction[0]*multiplier, column + (direction[1]*multiplier))
                    for position in to_flip:
                      self.to_flip.append(position)
                    self.valid = True
                    self.current_tile_nodes.append(current_tile)
                  to_flip.append((row + direction[0]*multiplier, column + (direction[1]*multiplier)))
                  multiplier +=1
    #logger.info(self.valid)
    return self.valid, self.current_tile_nodes, self.to_flip
  
     
    
  def highlight_tile(self):
    valid_tile_nodes=[]
    valid_tiles=[]
    valid_flip=[]
    active_node=self.current_gs
    
    core = self.core
    logger = self.logger
    self.namespace = None
    META = self.META
    
    
    
    '''
    nodesList = core.load_sub_tree(active_node)
    current_player = self.nodes[core.get_pointer_path(active_node, "currentPlayer")]
    current_player_color = core.get_attribute(current_player, 'color')
    logger.info(current_player_color)
    '''
    
    child_paths=core.get_children_paths(active_node)
    #old_player = core.get_pointer_path(copied_node, "currentPlayer")
    for child_path in child_paths:
      child=core.load_by_path(self.root_node,child_path)
      if core.is_instance_of(child, META["Board"]):
        board = child
        tile_paths = core.get_children_paths(board)
        for tile_path in tile_paths:
          
          tile = core.load_by_path(self.root_node, tile_path)
          if core.is_instance_of(tile,META["Tile"]):
          #logger.info("row: {0} column: {1}".format(core.get_attribute(tile,'row'),core.get_attribute(tile,'column')))
            valid,current_tiles,flip=self.next_move_viable(tile)
            
            if(valid==True):
              logger.debug('valid: {}'.format(valid))
              logger.debug('row:{0}'.format(core.get_attribute(tile,'row')))
              logger.debug('column:{0}'.format(core.get_attribute(tile,'column')))
              logger.info(flip)
              valid_tile_nodes.append(tile)
              valid_flip.append(flip)
    for i in valid_tile_nodes:
      valid_tiles.append([core.get_attribute(i,'row'),core.get_attribute(i,'column')])
    logger.info(valid_tiles)
    return valid_tile_nodes,valid_flip
  
  def auto_make_new_state(self,auto_tile,auto_flip):
     
    core = self.core
    logger = self.logger
    META = self.META
    nodes = self.nodes
    #logger.info(self.to_flip)
    #logger.debug(auto_tile)
    #_,_, this_flip=self.next_move_viable(auto_tile)
    #self.this_flip=this_flip
    #logger.info(this_flip)
   
    parent_state=self.current_gs
    game_folder = core.get_parent(parent_state)
    
    
    self.auto_row = core.get_attribute(auto_tile, 'row')
    self.auto_column = core.get_attribute(auto_tile, 'column')
    #core.create_node({'parent':game_folder, 'base': META["OthelloGameState"]})
    parent_name = core.get_attribute(parent_state, 'name')
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
    copied_node = core.copy_node(parent_state,game_folder)
    self.copied_node=copied_node
    core.set_pointer(copied_node,'previousGameState',parent_state) #pointing the previous pointer to old gamestate
    core.set_pointer(game_folder,'currentGameState',copied_node)# pointing the current pointer to the new gamestate
    core.set_attribute(copied_node, 'name', new_name)
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
          if core.get_attribute(tile, 'row') ==self.auto_row and core.get_attribute(tile, 'column') ==self.auto_column:
            created_piece = core.create_node({'parent':tile, 'base': META["Piece"]})
            core.set_pointer(copied_node, "currentMove", created_piece)
            core.set_attribute(created_piece, 'color', self.next_move_color)
          
          elif (core.get_attribute(tile, 'row'), core.get_attribute(tile, 'column')) in auto_flip:
            piece_path = core.get_children_paths(tile)[0]
            core.set_attribute(core.load_by_path(self.root_node, piece_path), 'color', self.next_move_color)
    
    
    #core.set_pointer(game_state, 'currentPlayer', player_node)
    self.util.save(self.root_node, self.commit_hash, self.branch_name)    
   
  def auto(self):
    from random import randrange
    active_node=self.current_gs
    core = self.core
    logger = self.logger
    valid_tiles=[]
    self.namespace = None
    META = self.META
    tiles,flips=self.highlight_tile()
    random_index = randrange(len(tiles))
    self.auto_make_new_state(tiles[random_index],flips[random_index])
    '''for tile in tiles:
      row=core.get_attribute(tile,'row')
      column=core.get_attribute(tile,'column')
      valid_tiles.append([row,column])
    logger.info(valid_tiles)'''
      
    
    #logger.info("row {0} column {1}".format(core.get_attribute(tile[0],'row'),core.get_attribute(tile[0],'column')))
    
#self.make_new_state(tile[0])
    
  
          
  
  
  def count_color(self):
    active_node=self.current_gs
    core = self.core
    logger = self.logger
    self.namespace = None
    META = self.META
    black_count=0
    white_count=0
    cp_list=self.core.get_children_paths(active_node)
    
    #self.logger.info('Childs of Game State {0}'.format(self.core.get_attribute(cp_list,'name')))
    for cp in cp_list:
      child=self.nodes[cp]
      #self.logger.info('Childs of Game State {0}'.format(self.core.get_attribute(child,'name')))
      #self.META['Board']
      if (self.core.is_instance_of(child, self.META['Board'])):
        for tile in self.core.get_children_paths(child):
          #self.logger.info(tile)
          tile=self.nodes[tile]
          for piece_path in self.core.get_children_paths(tile):
            piece=self.nodes[piece_path]           
            if "black"==self.core.get_attribute(piece,'color'):
              black_count=black_count+1
            elif "white"==self.core.get_attribute(piece,'color'):
              white_count=white_count+1
              
    logger.info(black_count)
    logger.info(white_count)
    
    return black_count,white_count
  
 
    
    
    
    
  def undo(self):
      active_node=self.active_node 
      core = self.core
      logger = self.logger
      self.namespace = None
      META = self.META
      nodesList = core.load_sub_tree(active_node)
    
      nodes = {}
      game_states=[]
      for node in nodesList:
        nodes[core.get_path(node)] = node
         
      current_gs_path=core.get_pointer_path(active_node,'currentGameState')
      current_gs=nodes[current_gs_path]
      logger.info(core.get_attribute(current_gs,'name'))
      prev_state_path=core.get_pointer_path(current_gs,'previousGameState')
      prev_state=nodes[prev_state_path]#doubtfull
      core.set_pointer(active_node,'currentGameState',prev_state)
      core.delete_node(current_gs)
      self.util.save(self.root_node,self.commit_hash,self.branch_name)
      
   
      
   
