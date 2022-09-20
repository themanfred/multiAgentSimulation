from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

from random import randint

def countAgentsPorSemaforo(model):
  lista = []
  carros = peatones = 0
  
  lista.append((len(model.grid.get_neighbors((2,0), False, True, 0)) + len(model.grid.get_neighbors((3,0), False, True, 0)), len(model.grid.get_neighbors((1,1), False, True, 0))))
  lista.append((len(model.grid.get_neighbors((0,4), False, True, 0)) + len(model.grid.get_neighbors((0,5), False, True, 0)), len(model.grid.get_neighbors((1,6), False, True, 0))))
  lista.append((len(model.grid.get_neighbors((7,2), False, True, 0)) + len(model.grid.get_neighbors((7,3), False, True, 0)), len(model.grid.get_neighbors((6,1), False, True, 0))))
  lista.append((len(model.grid.get_neighbors((4,7), False, True, 0)) + len(model.grid.get_neighbors((5,7), False, True, 0)), len(model.grid.get_neighbors((6,6), False, True, 0))))

  return lista

# TODOS LOS AGENTES CRUZARON
def all_agents_crossed(model):
  count = 0
  for despCell in model.despawnCellsCarros:
    agents = model.grid.get_neighbors(despCell, False, True, 0)
    count += len(agents)
  return count == model.num_carros

class Admin(Agent):
  def __init__(self, unique_id, model, cambio):
    super().__init__(unique_id, model)
    
    s1 = model.grid.get_neighbors((2,1), False, True, 0)[0]
    s2 = model.grid.get_neighbors((1,5), False, True, 0)[0]
    s3 = model.grid.get_neighbors((6,2), False, True, 0)[0]
    s4 = model.grid.get_neighbors((5,6), False, True, 0)[0]

    self.semaforos = [s1,s2,s3,s4]

    for i in range(4):
      j = 1
      while (not isinstance(self.semaforos[i], Semaforo)):
        self.semaforos = model.grid.get_neighbors(self.model.spawnSemaforos[i], False, True, 0)[j]
        j += 1

    self.contador = 0
    self.state = 1
    self.temp = 1
    self.amarillo = 10
    self.cambio = cambio

  def step(self):
    agentesPorSemaforo = countAgentsPorSemaforo(self.model)

    all_cars_crossed = True
    for i in range(len(agentesPorSemaforo)):
      if(agentesPorSemaforo[i][0] != 0): all_cars_crossed = False
    if(all_cars_crossed):
      self.state = 3
      return

    hay_peatones_esperando = False
    for i in range(len(agentesPorSemaforo)):
      if(agentesPorSemaforo[i][1] >= 5): hay_peatones_esperando = True
    
    if(hay_peatones_esperando):
      if(self.amarillo != 0):
        self.amarillo -= 1
      else: 
        self.state = 3
        self.amarillo = 5
      return

    if(self.contador > self.cambio):
      if(self.amarillo != 0):
        self.amarillo -= 1
        self.state = -1
        return
      self.contador = 0
      self.amarillo = 5
      if(self.temp == 1): self.state = 2
      elif(self.temp == 2): self.state = 3
      elif(self.temp == 3): self. state = 1
    else:
      self.contador += 1
      self.temp = self.state

  def advance(self):
    if(self.state == 1):
      self.semaforos[0].estado = 0
      self.semaforos[1].estado = 1
      self.semaforos[2].estado = 1
      self.semaforos[3].estado = 0
    elif(self.state == 2):
      self.semaforos[0].estado = 1
      self.semaforos[1].estado = 0
      self.semaforos[2].estado = 0
      self.semaforos[3].estado = 1
    elif(self.state == 3 or self.state == -1):
      self.semaforos[0].estado = 0
      self.semaforos[1].estado = 0
      self.semaforos[2].estado = 0
      self.semaforos[3].estado = 0

# SEMAFORO
class Semaforo(Agent):
  """
  0: rojo
  1: verde
  """
  def __init__(self, unique_id, model):
    super().__init__(unique_id, model)
    self.estado = 0
  
  def step(self):
    return

# CARRO
class Carro(Agent):
  def __init__(self, unique_id, model, pos, prioridad):
    super().__init__(unique_id, model)
    self.admin = self.model.grid.get_neighbors(self.model.spawnAgent, False, True, 0)[0]

    trayectorias = {(2,0):(0,2), (3,0):(3,7),
                    (0,4):(7,4), (0,5):(2,7),
                    (4,7):(4,0), (5,7):(7,5),
                    (7,2):(5,0), (7,3):(0,3)}

    self.pos = pos
    self.dest = trayectorias[pos]
    self.next_pos = pos
    self.first_move = True
    self.medio = (0,0)
    self.ha_tocado_medio = False
    self.can_cross = False
    self.pos_origen = pos
    self.prioridad = prioridad

    if(self.pos == (2,0)): self.medio = (2,2)
    elif(self.pos == (0,5)): self.medio = (2,5)
    elif(self.pos == (5,7)): self.medio = (5,5)
    elif(self.pos == (7,2)): self.medio = (5,2) 

  def step(self):
    if(self.pos_origen in [(0,4),(0,5),(7,2),(7,3)] and self.admin.state == 1):
      self.can_cross = True
    elif(self.pos_origen in [(2,0),(3,0),(4,7),(5,7)] and self.admin.state == 2):
      self.can_cross = True

    if(not self.can_cross): return
    
    if(self.pos in self.model.despawnCellsCarros or self.first_move): 
      self.first_move = False
      self.is_crossing = False
      return
    self.is_crossing = True
    temp = self.pos

    if(self.prioridad != 0):
      self.prioridad -= 1
      self.can_cross = False
      return

    # si esta en un carril que va recto
    if(self.pos[0] == self.dest[0] or self.pos[1] == self.dest[1]):
      if(self.pos[0] == self.dest[0]):
        mov = 1 if self.pos[1] < self.dest[1] else -1
        temp = (self.pos[0], self.pos[1] + mov)
      else:
        mov = 1 if self.pos[0] < self.dest[0] else -1
        temp = (self.pos[0] + mov, self.pos[1])
    else: # dan vuelta a la izquierda
      if(not self.ha_tocado_medio):
        if(self.pos[0] == self.medio[0]):
          mov = 1 if self.pos[1] < self.medio[1] else -1
          temp = (self.pos[0], self.pos[1] + mov)
        else:
          mov = 1 if self.pos[0] < self.medio[0] else -1
          temp = (self.pos[0] + mov, self.pos[1])
      else:
        if(self.pos[0] == self.dest[0]):
          mov = 1 if self.pos[1] < self.dest[1] else -1
          temp = (self.pos[0], self.pos[1] + mov)
        else:
          mov = 1 if self.pos[0] < self.dest[0] else -1
          temp = (self.pos[0] + mov, self.pos[1])
    self.next_pos = temp
      
  def advance(self):
    self.model.grid.move_agent(self, self.next_pos)
    self.pos = self.next_pos

#PEATON
class Peaton(Agent):
  def __init__(self, unique_id, model, pos, origen, destino, prioridad):
    super().__init__(unique_id, model) 
    self.origen = origen
    self.destino = destino
    self.pos = pos
    self.next_pos = pos
    self.first_move = True
    self.is_crossing = False
    self.admin = self.model.grid.get_neighbors(self.model.spawnAgent, False, True, 0)[0]
    self.prioridad = prioridad
    self.hidden = prioridad != 0
    self.wait = False
  
  def step(self):
    if(self.first_move):
      self.first_move = False
      return

    if(self.pos in self.model.despawnCellsPeatones or (not self.is_crossing and self.admin.state != 3)): 
      self.wait = False
      return

    if(self.wait): return

    if(self.prioridad != 0):
      self.wait = True
      self.prioridad -= 1
      self.hidden = True
      return

      self.hidden = False

    if(self.origen == 1): 
      if(self.destino == 2): temp_pos = (self.pos[0], self.pos[1]+1)
      elif(self.destino == 3): temp_pos = (self.pos[0]+1, self.pos[1])
      elif(self.destino == 4): temp_pos = (self.pos[0]+1, self.pos[1]+1)
    elif(self.origen == 2):
      if(self.destino == 1): temp_pos = (self.pos[0], self.pos[1]-1)
      elif(self.destino == 3): temp_pos = (self.pos[0]+1, self.pos[1]-1)
      elif(self.destino == 4): temp_pos = (self.pos[0]+1, self.pos[1])
    elif(self.origen == 3):
      if(self.destino == 1): temp_pos = (self.pos[0]-1, self.pos[1])
      elif(self.destino == 2): temp_pos = (self.pos[0]-1, self.pos[1]+1)
      elif(self.destino == 4): temp_pos = (self.pos[0], self.pos[1]+1)
    elif(self.origen == 4):
      if(self.destino == 1): temp_pos = (self.pos[0]-1, self.pos[1]-1)
      elif(self.destino == 2): temp_pos = (self.pos[0]-1, self.pos[1])
      elif(self.destino == 3): temp_pos = (self.pos[0], self.pos[1]-1) 

    self.next_pos = temp_pos
    
  def advance(self):
    self.model.grid.move_agent(self, self.next_pos)
    self.pos = self.next_pos

#INTERSECCION
class Interseccion(Model):
  def __init__(self, num_carros, num_peatones):
    self.num_carros = num_carros
    self.num_peatones = num_peatones
    self.grid = MultiGrid(8,8,False)
    self.schedule = SimultaneousActivation(self)
    self.i = 0

    self.spawnSemaforos = [(2,1), (1,5), (6,2), (5,6)]
    self.spawnPeatones = [(1,1), (1,6), (6,1), (6,6)]
    self.spawnCarros = [(2,0), (3,0), (0,4), (0,5), (4,7), (5,7), (7,2), (7,3)]
    self.spawnAgent = (3,5)

    self.despawnCellsPeatones = [(0,0), (0,1), (1,0), (6,0), (7,0), (7,1), (7,6), (7,7), (6,7), (0,6), (0,7), (1,7)]
    self.despawnCellsCarros = [(0,2), (0,3), (4,0), (5,0), (2,7), (3,7), (7,4), (7,5)]

    self.peatones = []
    self.carros = []
    self.semaforos = []

    # colocar agentes en sus spawns
    for pos in self.spawnSemaforos:
      s = Semaforo("S"+str(pos), self)
      self.semaforos.append(s)
      self.grid.place_agent(s, pos)
      self.schedule.add(s)

    a = Admin("Admin", self, 15)
    self.grid.place_agent(a, self.spawnAgent)
    self.schedule.add(a)

    for i in range(num_carros):
      pos = self.spawnCarros[randint(0,len(self.spawnCarros) - 1)]
      carros_esperando = len(self.grid.get_neighbors(pos , False, True, 0))
      c = Carro("C"+str(i), self, pos, carros_esperando) 
      self.carros.append(c)
      self.grid.place_agent(c, pos)
      self.schedule.add(c)
  
  def step(self):
    if(randint(0,10) == 0): 
      esquinaIni = randint(1,len(self.spawnPeatones)) 
      esquinaFin = randint(1,len(self.spawnPeatones)) 

      while(esquinaIni == esquinaFin):
        esquinaFin = randint(1,len(self.spawnPeatones))

      pos = self.spawnPeatones[esquinaIni - 1]
      dest = self.spawnPeatones[esquinaFin - 1]

      p = Peaton("P"+str(self.i), self, pos, esquinaIni, esquinaFin, 0) 
      self.peatones.append(p)
      self.grid.place_agent(p, pos)
      self.schedule.add(p)
      self.i += 1
      
    self.schedule.step()
    
  def status_peatones(self):
    data = []
    for p in self.peatones:
      data.append({'id': p.unique_id, 'next_pos': p.next_pos, 'is_hidden': p.hidden})
    return data

  def status_carros(self):
    data = []
    for c in self.carros:
      data.append({'id': c.unique_id, 'next_pos': c.next_pos, 'prioridad': c.prioridad})
    return data

  def status_semaforos(self):
    data = []
    for s in self.semaforos:
      data.append({'id': s.unique_id, 'estado': s.estado})
    return data
  
  def status_agents(self):
    data = []
    data.append(self.status_semaforos())
    data.append(self.status_peatones())
    data.append(self.status_carros())
    
    return data