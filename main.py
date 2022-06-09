import random

import numpy as np

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


class Reg:
    def __init__(self, value=None, busy=[]):
        self.value = value
        self.busyIds = busy

    def toString(self):
        return "[value: " + str(self.value) + ", busy: " + str(self.busyIds) + "]"


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
        if op == "LW" or op == "SW" or op == "ADD" or op == "SUB":
            self.clocks = 2
        elif op == "MUL":
            self.clocks = 10
        elif op == "DIV":
            self.clocks = 40
        self.clocksLeft = self.clocks

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


class Component:
    def __init__(self, limit):
        self.queue = []
        self.limit = limit

    def enqueue(self, element):
        if len(self.queue) < self.limit:
            # self.queue.append({"busyId": state, "element": element})
            self.queue.append(element)
        else:
            print("Component Full!")

    def dequeue(self, index=0):
        self.queue.pop(index)


cacheMemory = []
FPRegisters = {}
ARegisters = {}
LBuffers = Component(3)
SBuffers = Component(3)
addStations = Component(3)
mulStations = Component(2)

mixedMEMComponent = Component(6)
mixedALUComponent = Component(5)

instructions = []
instructionQueue = []
completedInstructionQueue = []


def generateCache():
    random.seed(1001)
    for i in range(0, 100):
        cacheMemory.append(random.randint(1, 200))


def generateComponents2():
    for i in range(0, 6):
        FPRegisters['F' + str(i)] = Reg()
    for i in range(0, 4):
        ARegisters['R' + str(i)] = Reg()


def printCache():
    for i in range(0, 100):
        print("["+str(i)+": "+ str(cacheMemory[i])+"]")


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
    print("-------Store Buffers:-------")
    for i in SBuffers.queue:
        print(i.toString())
    print("-------Load Buffers:-------")
    for i in LBuffers.queue:
        print(i.toString())
    print("-------Add/Sub Stations:-------")
    for i in addStations.queue:
        print(i.toString())
    print("-------Mul/Div Stations:-------")
    for i in mulStations.queue:
        print(i.toString())
    print("-------COMPLETED INSTRUCTIONS:-------")
    for i in completedInstructionQueue:
        print(i.toStringEco())

def printComponents2():
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


def parseInstruction(instruction):
    instructionArgs = str(instruction).split(" ")
    return Instruction(instructionArgs[0], instructionArgs[1], instructionArgs[2], instructionArgs[3])


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


''' '''


def convertReg(arg):
    if str(arg).__contains__("F"):
        number = FPRegisters[arg].value
    elif str(arg).__contains__("R"):
        number = ARegisters[arg].value
    else:
        number = int(arg)
    return number

def parseReg(arg):
    if str(arg).__contains__("F") or str(arg).__contains__("R"):
        number = int(arg[1])
    elif arg.type() == "int":
        number = arg
    return number

def simulaInsta():
    clocks = 0
    while len(instructionQueue) > 0:
        currArgs = parseInstruction(instructions[0])
        if currArgs.op == "LW":
            FPRegisters[currArgs.register].value = cacheMemory[int(currArgs.args1) + int(currArgs.args2)]
        elif currArgs.op == "ADD":
            FPRegisters[currArgs.register].value = convertReg(currArgs.args1) + convertReg(currArgs.args2)
        elif currArgs.op == "SUB":
            FPRegisters[currArgs.register].value = convertReg(currArgs.args1) - convertReg(currArgs.args2)
        elif currArgs.op == "MUL":
            FPRegisters[currArgs.register].value = convertReg(currArgs.args1) * convertReg(currArgs.args2)
        elif currArgs.op == "DIV":
            FPRegisters[currArgs.register].value = int(convertReg(currArgs.args1) / convertReg(currArgs.args2))
        clocks += 1
        print("-----------CLOCK " + str(clocks) + "-----------")
        instructionQueue.pop(0)
        printComponents()


def checkNotEnd():
    return len(instructionQueue) > 0 or len(LBuffers.queue) > 0 or len(SBuffers.queue) > 0 or len(
        addStations.queue) > 0 or len(mulStations.queue) > 0

def checkNotEnd2():
    return len(instructionQueue) > 0 or len(mixedMEMComponent.queue) > 0 or len(mixedALUComponent.queue) > 0


def issueInstruction(component, instruction):
    if len(component.queue) < component.limit:
        instruction.isIssued = True
        component.enqueue(instruction)
        instructionQueue.pop(0)

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

def tomasuloBehaviorMem(queue, currBufferInst, runningClocks, i):
    targetRegister = FPRegisters[currBufferInst.register]
    if currBufferInst.busyId == 0:  # reserva o lugar na fila do registrador
        busyId = random.random()
        currBufferInst.busyId = busyId
        FPRegisters[currBufferInst.register].busyIds.append(busyId)
        # print("========SWITCHING BUSY TO " + str(busyId) + " FOR INSTR: "+ currBufferInst.toStringEco() +"===========")
    elif targetRegister.busyIds[0] == currBufferInst.busyId:
        if not currBufferInst.isStartedDetect:  # se não tiver começado
            currBufferInst.isStartedDetect = True
        else:
            if not currBufferInst.isStarted:  # marca momento de start
                currBufferInst.isStarted = True
                currBufferInst.isStartedClock = runningClocks
            if currBufferInst.clocksLeft > 0:  # se ainda está executando a operação
                currBufferInst.clocksLeft -= 1
            else:
                if not currBufferInst.isFinished:
                    currBufferInst.isFinished = True
                    currBufferInst.isFinishedClock = runningClocks
                    tomasuloOperation(currBufferInst) # faz operação
                # libera registrador:
                if not currBufferInst.isWrittenDetect:  # flag para marcar written no próximo clock
                    currBufferInst.isWrittenDetect = True
                else:
                    currBufferInst.isWritten = True
                    currBufferInst.isWrittenClock = runningClocks
                    FPRegisters[currBufferInst.register].busyIds.pop(0)
                    currBufferInst.busyId = 0
                    completedInstructionQueue.append(currBufferInst)
                    queue.pop(i)
                    i -= 1
    return i


def tomasuloBehaviorALU(queue, currBufferInst, runningClocks, i):
    targetRegister = FPRegisters[currBufferInst.register]
    operandReg1 = FPRegisters[currBufferInst.args1]
    operandReg2 = FPRegisters[currBufferInst.args2]
    if currBufferInst.busyId == 0:  # reserva lugar na fila dos registradores
        busyId = random.random()
        currBufferInst.busyId = busyId
        FPRegisters[currBufferInst.register].busyIds.append(busyId)
        FPRegisters[currBufferInst.args1].busyIds.append(busyId)
        FPRegisters[currBufferInst.args2].busyIds.append(busyId)
        #print("========SWITCHING BUSY TO " + str(busyId) + " FOR INSTR: "+ currBufferInst.toStringEco() +"===========")
    elif targetRegister.busyIds[0] == currBufferInst.busyId and operandReg1.busyIds[0] == currBufferInst.busyId and operandReg2.busyIds[0] == currBufferInst.busyId:
        if not currBufferInst.isStartedDetect:  # se não tiver começado
            currBufferInst.isStartedDetect = True
        else:  # marca momento de start
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
                else:
                    if not currBufferInst.isWrittenDetect:  # flag para marcar written no próximo clock
                        currBufferInst.isWrittenDetect = True
                    else:
                        currBufferInst.isWritten = True
                        currBufferInst.isWrittenClock = runningClocks
                        FPRegisters[currBufferInst.register].busyIds.pop(0)
                        FPRegisters[currBufferInst.args1].busyIds.pop(0)
                        FPRegisters[currBufferInst.args2].busyIds.pop(0)
                        currBufferInst.busyId = 0
                        completedInstructionQueue.append(currBufferInst)
                        queue.pop(i)
                        i -= 1
    return i

def fetchInstructions1(runningClocks):
    # instruction fetcher
    if len(instructionQueue) > 0:
        currInstructionFetch = instructionQueue[0]
        if currInstructionFetch.op == "LW":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(LBuffers, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "SW":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(SBuffers, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "ADD":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(addStations, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "SUB":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(addStations, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "MUL":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mulStations, currInstructionFetch)
            # else stall
        elif currInstructionFetch.op == "DIV":
            currInstructionFetch.isIssuedClock = runningClocks
            issueInstruction(mulStations, currInstructionFetch)
            # else stall

def fetchInstructions2(runningClocks):
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

def runComponents1(runningClocks):
    # LBuffer execution
    if len(LBuffers.queue) > 0:
        i = 0
        while i < len(LBuffers.queue):
            currBufferInst = LBuffers.queue[i]
            i = tomasuloBehaviorMem(LBuffers.queue, currBufferInst, runningClocks, i)
            i += 1
    # /LBuffer

    # SBuffer execution
    if len(SBuffers.queue) > 0:
        i = 0
        while i < len(SBuffers.queue):
            currBufferInst = SBuffers.queue[i]
            i = tomasuloBehaviorMem(SBuffers.queue, currBufferInst, runningClocks, i)
            i += 1
    # /SBuffer

    # addStations execution
    if len(addStations.queue) > 0:
        i = 0
        while i < len(addStations.queue):
            currBufferInst = addStations.queue[i]
            i = tomasuloBehaviorALU(addStations.queue, currBufferInst, runningClocks, i)
            i += 1
    # /addStations

    # mulStations execution
    if len(mulStations.queue) > 0:
        i = 0
        while i < len(mulStations.queue):
            currBufferInst = mulStations.queue[i]
            i = tomasuloBehaviorALU(mulStations.queue, currBufferInst, runningClocks, i)
            i += 1
    # /mulStations
def runComponents2(runningClocks):
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

def simulasulo():
    runningClocks = 1
    while checkNotEnd2() and runningClocks < 200:

        fetchInstructions2(runningClocks)
        runComponents2(runningClocks)


        print("-----------CLOCK " + str(runningClocks) + "-----------")
        printComponents2()
        runningClocks += 1


def app():
    generateCache()
    generateComponents2()
    generateInstructions()
    printCache()
    FPRegisters["F4"].value = 2
    print("-----------CLOCK 0-----------")
    printComponents()
    simulasulo()

#DRIVER
app()


# --

# PRECISA FAZER O BUSY DO REGISTRADOR SER UMA FILA DE BUSYS DAS OPERAÇÕES CONFORME ELAS CHEGAM PRA REQUISITAR O REGISTRADOR.
#feito

# POR QUÊ TODOS OS REGISTRADORES RECEBEM OS BUSYS IGUALEMENTE???????????????????