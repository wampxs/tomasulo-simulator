import random

'''
---------------
-TOMASULO-

LW DESTINO VAL1 VAL2
-carrega, da cache, palavra no endereço VAL1+VAL2 e armazena no registrador DESTINO
-- VAL pode ser número ou registrador
SW ORIGEM VAL1 VAL2
-armazena, na cache, palavra do registrador ORIGEM no endereço VAL1+VAL2
ADD DESTINO VAL1 VAL2
-performa adição entre VAL1 e VAL2, guardando resultado no registrador DESTINO
SUB DESTINO VAL1 VAL2
-performa subtração entre VAL1 e VAL2, guardando resultado no registrador DESTINO
MUL DESTINO VAL1 VAL2
-performa multiplicação entre VAL1 e VAL2, guardando resultado no registrador DESTINO
DIV DESTINO VAL1 VAL2
-performa divisão entre VAL1 e VAL2, guardando resultado no registrador DESTINO

---------------

LW  - 2 CLOCKS
SW  - 2 CLOCKS
ADD - 2 CLOCKS
SUB - 2 CLOCKS
MUL - 10 CLOCKS
DIV - 40 CLOCKS

---------------

Instruction Queue 
- Fila de instruções. A cada clock, envia a próxima instrução para o pipeline, caso seja possível. Se não, stall
Address Registers
- Registradores para armazenar endereços da cache
FP Registers
- Registradores para armazenar valores numéricos (float ou não)
Load e Store Buffers
- Buffers que conterão endereços pendentes para operações de load e store (guardam endereço da cache e registrador)
Reservation Stations (Add/Sub e Mul/Div)
- Buffers que conterão operações aritméticas pendentes (guardam registrador e operandos)

-- Cada estrutura acima possui seus componentes de processamento (ULAs e MMUs, por exemplo), que concluem operações
   em seus devidos tempos de clock.
'''

# Define o tempo de clock de cada operação
clockTimeDict = {"LW":2,"SW":2,"ADD":2,"SUB":2,"MUL":10,"DIV":40}
def printClockTimes():
    for i in clockTimeDict.items():
        print(i[0]+": "+str(i[1]))

# Classe que descreve um registrador.
# Possui um ID, o valor contido no registrador, e uma fila de IDs de ocupado
# A fila recebe IDs únicos de instruções que desejam acessar o registrador
# e garante o controle para que apenas a instrução no começo da fila manipule-o a cada dado momento.

class Reg:
    def __init__(self, regid, value=None, busy=[]):
        self.regid = regid
        self.value = value
        self.busyIds = busy

    def toString(self):
        return "[id : " +str(self.regid)+", value: " + str(self.value) + ", busy: " + str(self.busyIds) + "]"

    def appendBusyID(self,busyid):
        array = []
        array = self.busyIds.copy()
        array.append(busyid)
        self.busyIds = array.copy()
    def popBusyID(self):
        self.busyIds.pop(0)

# A classe Instruction armazena todos os valores necessários para a realização correta de uma instrução.
# Contém também um ID de ocupado, que é enviado a registradores para garantir sua execução exclusiva sobre o mesmo.

class Instruction:
    def __init__(self, op, register, args1, args2):
        self.op = op
        self.register = register
        self.args1 = args1
        self.args2 = args2
        self.isIssued = False
        self.isStarted = False
        self.isFinished = False
        self.isWritten = False
        self.isIssuedClock = -1
        self.isStartedClock = -1
        self.isFinishedClock = -1
        self.isWrittenClock = -1
        self.isWrittenDetect = False
        self.isStartedDetect = False
        self.busyId = 0
        self.clocks = 0
        self.clocks = clockTimeDict[op]
        self.clocksLeft = clockTimeDict[op]

    def toString(self):
        return "[op: " + str(self.op) + ", register: " + str(self.register) + ", args1: " + str(
            self.args1) + ", args2:" + str(self.args2) + ", isIssued: " + str(self.isIssued) + ", isStarted: " + str(
            self.isStarted) + ", isFinished: " + str(self.isFinished) + ", isWritten: " + str(
            self.isWritten) + ", busyId: " + str(
            self.busyId) + ", clocks: " + str(self.clocks) + ", clocksLeft: " + str(
            self.clocksLeft) + ", isIssuedClock: " + str(self.isIssuedClock) + ", isStartedClock: " + str(
            self.isStartedClock) + ", isFinishedClock: " + str(self.isFinishedClock) + ", isWrittenClock: " + str(
            self.isWrittenClock) + "]"

    def toStringEco(self):
        return "[instruction: " + str(self.op) + " " + str(self.register) + " " + str(self.args1) + " " + str(
            self.args2) + ", isIssuedClock: " + str(self.isIssuedClock) + ", isStartedClock: " + str(
            self.isStartedClock) + ", isFinishedClock: " + str(self.isFinishedClock) + ", isWrittenClock: " + str(
            self.isWrittenClock) + "]"


# A classe Component descreve um componente do circuito, sendo capaz de armazenar instruções em um buffer
# Cada componente executa as instruções em seu buffer paralelamente.
# Caso o buffer esteja cheio, a instrução permanece na fila de instruções até liberar espaço para que ela seja enviada.

class Component:
    def __init__(self, limit):
        self.queue = []
        self.limit = limit

    def enqueue(self, element):
        if len(self.queue) < self.limit:
            self.queue.append(element)
        else:
            print("Component Full!")

    def dequeue(self, index=0):
        self.queue.pop(index)

# Cache simulada
cacheMemory = []

# Registradores (chave de "Fx":Reg(), com 'x' sendo o ID do registrador).

FPRegisters = {}
ARegisters = {}

# Componentes

mixedMEMComponent = Component(6) # Componente para operações de memória (LW/SW)
mixedALUComponent = Component(5) # Componente para operações aritméticas (ADD/SUB/MUL/DIV)

# Controle de Instruções

instructions = []
instructionQueue = []
completedInstructionQueue = []


# Gera uma cache aleatória de N elementos

def generateCache(n):
    random.seed(1001)
    for i in range(0, n):
        cacheMemory.append(random.randint(1, 200))

# Preenche as chaves de registradores com instâncias da classe Reg

def generateComponents():
    for i in range(0, 6):
        FPRegisters['F' + str(i)] = Reg(i)
    for i in range(0, 4):
        ARegisters['R' + str(i)] = Reg(i)

# Imprime a Cache

def printCache():
    for i in range(0, 100):
        print("["+str(i)+": "+ str(cacheMemory[i])+"]")

# Imprime todos os componentes do circuito

def printComponents():
    print("-------Instruction Queue:-------")
    for i in instructionQueue:
        print(i.toString())
    print("-------FP Registers:-------")
    for i in FPRegisters.items():
        print(str(i[0]) + ": " + str(i[1].toString()))
    print("-------Address Registers:-------")
    for i in ARegisters.items():
        print(str(i[0]) + ": " + str(i[1].toString()))
    print("-------Memory Buffers:-------")
    for i in mixedMEMComponent.queue:
        print(i.toString())
    print("-------ALU Stations:-------")
    for i in mixedALUComponent.queue:
        print(i.toString())
    print("-------COMPLETED INSTRUCTIONS:-------")
    for i in completedInstructionQueue:
        print(i.toStringEco())

# Interpreta uma string de instrução, transformando-a em um objeto Instruction funcional

def parseInstruction(instruction):
    instructionArgs = str(instruction).split(" ")
    return Instruction(instructionArgs[0], instructionArgs[1], instructionArgs[2], instructionArgs[3])

# Geração de Instruções

def generateInstructions():
    instructions.append("LW F0 24 42")
    instructions.append("LW F1 34 42")
    instructions.append("LW F2 45 45")
    instructions.append("LW F3 31 42")
    instructions.append("LW F4 41 45")
    instructions.append("LW F5 30 42")
    instructions.append("MUL F3 F2 F1")
    instructions.append("SUB F5 F1 F2")
    instructions.append("DIV F0 F3 F1")
    instructions.append("ADD F1 F5 F2")
    for i in instructions:
        instructionQueue.append(parseInstruction(i))


def generateInstructionsTest():
    instructions.append("LW F1 34 42")
    instructions.append("LW F2 45 45")
    instructions.append("MUL F3 F2 F1")
    instructions.append("SUB F5 F1 F2")
    instructions.append("DIV F0 F3 F1")
    instructions.append("ADD F1 F5 F2")
    for i in instructions:
        instructionQueue.append(parseInstruction(i))

#/Geração de Instruções

###

# Interpreta o nome de um registrador passado em uma instrução, podendo ser um endereço de registrador ou número inteiro

def convertReg(arg):
    if str(arg).__contains__("F"):
        number = FPRegisters[arg].value
    elif str(arg).__contains__("R"):
        number = ARegisters[arg].value
    else:
        number = int(arg)
    return number

# Retorna um valor boolean que indica se a simulação finalizou ou não

def checkNotEnd():
    return len(instructionQueue) > 0 or len(mixedMEMComponent.queue) > 0 or len(mixedALUComponent.queue) > 0

# Encomenda uma instrução para um componente, caso haja espaço.

def issueInstruction(component, instruction):
    if len(component.queue) < component.limit:
        instruction.isIssued = True
        component.enqueue(instruction)
        instructionQueue.pop(0)

# Resgata instruções da fila e direciona-as para o componente correspondente

def fetchInstructions(runningClocks):
    # instruction fetcher
    if len(instructionQueue) > 0:
        currInstructionFetch = instructionQueue[0]
        if currInstructionFetch.op == "LW":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedMEMComponent, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "SW":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedMEMComponent, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "ADD":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedALUComponent, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "SUB":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedALUComponent, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "MUL":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedALUComponent, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "DIV":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mixedALUComponent, currInstructionFetch)
            # else stall


# Efetua a operação de uma instrução

def tomasuloOperation(currBufferInst):
    targetRegister = FPRegisters[currBufferInst.register]
    if currBufferInst.op == "LW":
        targetRegister.value = cacheMemory[convertReg(currBufferInst.args1) + convertReg(currBufferInst.args2)]  # load
    elif currBufferInst.op == "SW":
        cacheMemory[convertReg(currBufferInst.args1) + convertReg(currBufferInst.args2)] = targetRegister.value  # store
    elif currBufferInst.op == "ADD":
        targetRegister.value = convertReg(currBufferInst.args1) + convertReg(currBufferInst.args2)  # add
    elif currBufferInst.op == "SUB":
        targetRegister.value = convertReg(currBufferInst.args1) - convertReg(currBufferInst.args2)  # sub
    elif currBufferInst.op == "MUL":
        targetRegister.value = convertReg(currBufferInst.args1) * convertReg(currBufferInst.args2)  # mul
    elif currBufferInst.op == "DIV":
        if not convertReg(currBufferInst.args2) == 0:
            targetRegister.value = convertReg(currBufferInst.args1) / convertReg(currBufferInst.args2)  # divSBuffer
        else:
            targetRegister.value = 0

# Comportamento do componente de instruções de memória.

def tomasuloBehaviorMem(queue, currBufferInst, runningClocks, i):
    targetRegister = FPRegisters[currBufferInst.register]
    if currBufferInst.busyId == 0:  # reserva o lugar na fila do registrador
        busyId = random.random()    # gera um id único
        currBufferInst.busyId = busyId
        targetRegister.appendBusyID(busyId)
    elif targetRegister.busyIds[0] == currBufferInst.busyId:    # se é a vez dessa instrução operar no registrador...
        if not currBufferInst.isStarted:    # marca momento de start
            currBufferInst.isStarted = True
            currBufferInst.isStartedClock = runningClocks
        if currBufferInst.clocksLeft > 0:   # se ainda está executando a operação
            currBufferInst.clocksLeft -= 1
        else:   # se já finalizou a operação...
            if not currBufferInst.isFinished:   # marca momento de finish
                currBufferInst.isFinished = True
                currBufferInst.isFinishedClock = runningClocks
                tomasuloOperation(currBufferInst)   # faz a operação
            # libera registrador:
            if not currBufferInst.isWrittenDetect:  # flag para marcar written no próximo clock
                currBufferInst.isWrittenDetect = True
            else:
                currBufferInst.isWritten = True
                currBufferInst.isWrittenClock = runningClocks
                targetRegister.popBusyID()
                currBufferInst.busyId = 0
                completedInstructionQueue.append(currBufferInst)
                queue.pop(i)
                i -= 1
    return i


# Comportamento do componente de instruções aritméticas.
# Efetivamente igual ao comportamento de memória, exceto ser necessário reservar os 3 registradores da instrução


def tomasuloBehaviorALU(queue, currBufferInst, runningClocks, i):
    targetRegister = FPRegisters[currBufferInst.register]
    operandReg1 = FPRegisters[currBufferInst.args1]
    operandReg2 = FPRegisters[currBufferInst.args2]
    if currBufferInst.busyId == 0:  # reserva lugar na fila dos registradores
        busyId = random.random()
        currBufferInst.busyId = busyId
        targetRegister.appendBusyID(busyId)
        operandReg1.appendBusyID(busyId)
        operandReg2.appendBusyID(busyId)
    elif targetRegister.busyIds[0] == currBufferInst.busyId and operandReg1.busyIds[0] == currBufferInst.busyId and operandReg2.busyIds[0] == currBufferInst.busyId:
        if not currBufferInst.isStarted:
            currBufferInst.isStarted = True
            currBufferInst.isStartedClock = runningClocks
        if currBufferInst.clocksLeft > 0:  # se ainda está executando a operação
            currBufferInst.clocksLeft -= 1
        else:
            if not currBufferInst.isFinished:
                currBufferInst.isFinished = True
                currBufferInst.isFinishedClock = runningClocks
                tomasuloOperation(currBufferInst)
            if not currBufferInst.isWrittenDetect:  # flag para marcar written no próximo clock
                currBufferInst.isWrittenDetect = True
            else:
                currBufferInst.isWritten = True
                currBufferInst.isWrittenClock = runningClocks
                targetRegister.popBusyID()
                operandReg1.popBusyID()
                operandReg2.popBusyID()
                currBufferInst.busyId = 0
                completedInstructionQueue.append(currBufferInst)
                queue.pop(i)
                i -= 1
    return i


# Efetua execução dos componentes do circuito

def runComponents(runningClocks):
    if len(mixedMEMComponent.queue) > 0:
        i = 0
        while i < len(mixedMEMComponent.queue):
            currBufferInst = mixedMEMComponent.queue[i]
            i = tomasuloBehaviorMem(mixedMEMComponent.queue, currBufferInst, runningClocks, i)
            i += 1
    if len(mixedALUComponent.queue) > 0:
        i = 0
        while i < len(mixedALUComponent.queue):
            currBufferInst = mixedALUComponent.queue[i]
            i = tomasuloBehaviorALU(mixedALUComponent.queue, currBufferInst, runningClocks, i)
            i += 1

# Função que contém a simulação

def simulasulo():
    runningClocks = 1
    while checkNotEnd():
        fetchInstructions(runningClocks)
        runComponents(runningClocks)
        print("-----------CLOCK " + str(runningClocks) + "-----------")
        printComponents()
        runningClocks += 1


# Função que contém todos os procedimentos para a conclusão correta da simulação

def app():
    generateCache(100)
    generateComponents()
    generateInstructionsTest()
    printCache()
    FPRegisters["F4"].value = 2
    print("-----------CLOCK 0-----------")
    printComponents()
    simulasulo()
    print("\n")
    printClockTimes()


# DRIVER

app()
