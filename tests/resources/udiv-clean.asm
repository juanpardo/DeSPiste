PREAD = 12584960
PWRTE = 12584960
MVI PREAD,PL
ADD				NOP					MOV ALU,A		MOV 62,CT3
SL				NOP					MOV ALU,A		NOP
NOP				NOP					NOP				MOV ALL,RA0
NOP				NOP					CLR A			MOV ALL,MC3
MVI PWRTE,PL
ADD				NOP					MOV ALU,A		NOP
SL				NOP					MOV ALU,A		NOP
NOP				NOP					NOP				MOV ALL,WA0
NOP				NOP					CLR A			MOV ALL,MC3
NOP				NOP					NOP				MOV 0,CT0
NOP				NOP					NOP				MOV 0,CT1
NOP				NOP					NOP				MOV 0,CT2
NOP				NOP					NOP				MOV 0,CT3
DVE = 649
DVI = 49
MVI DVE,MC0
MVI DVI,MC0
mov 0,ct0
mov 0,ct1
mov 0,ct3
mvi 1,LOP
mvi DIVIDE,PC
nop
END
DIVIDE:
                mov mc0,p 									clr a			mov 0,ct1
ad2  			mov mc0,p 									mov alu,a		mov 1,mc1
                                                            clr a 			mov all,mc0
ad2 														mov alu,a
                                                            clr a 			mov all,mc0
                                                                            mov 2,ct0
                mov mc0,p									clr a
ad2				mov mc0,p 									mov alu,a		mov 0,ct1
sub 														clr a			mov 3,ct0
jmp ZS,DIVEND
mvi 0,mc1,s
jmp SLCOND:
SLLOOP:
                mov m0,p									clr a 			mov 0,ct1
ad2 														mov alu,a
sl 															mov alu,a
                mov m1,p									clr a			mov all,mc0
ad2															mov alu,a
sl															mov alu,a		mov 3,ct0
                                                            clr a			mov all,mc1
SLCOND:
                mov m0,p									clr a			mov 2,ct0
ad2				mov m0,p									mov alu,a
sl															mov alu,a
sub															mov alu,a		mov 0,ct1
jmp S,SLLOOP:
                                                            clr a			mov 3,ct0
                mov mc1,p
ad2				mov mc1,p									mov alu,a
ad2															mov alu,a		mov 1,ct1
                                                            clr a			mov all,mc1
                                                            clr a			mov 2,ct0
                mov mc0,p													mov 0,ct1
ad2				mov mc0,p									mov alu,a
sub															mov alu,a		mov 0,ct0
                                                                            mov all,mc0
jmp DIVIDE:
                                                                            mov 0,ct0
DIVEND:																		mov 0,ct1
mov mc1,p													clr a
ad2				mov mc1,p									mov alu,a		mov 0,ct0
ad2															mov alu,a		mov 1,ct1
                                                            clr a			mov all,mc1
                                                                            mov 1,ct1
DMA mc1,D0,3
BTM
