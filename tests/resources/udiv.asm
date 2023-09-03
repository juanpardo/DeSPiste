	PREAD = 12584960	; Constant to be changed by SH2 before program load.
	PWRTE = 12584960	; Constant to be changed by SH2 before program load.
	;------------------------------------------------------------------------ P64 PROGRAM DMA HEADER
	MVI PREAD,PL															; SH2 sets "PREAD" and "WRITE" constants before program load.
	ADD				NOP					MOV ALU,A		MOV 62,CT3			; MVI is 25-bit signed data. So it requires 3 shifts right to get high memory address in that bit depth.
	SL				NOP					MOV ALU,A		NOP					; As DSP reads data in DWORD units, the address actually must be on 4-byte boundaries,
	NOP				NOP					NOP				MOV ALL,RA0			; so we need to shift left one to get the proper address in RA0 and WA0.
	NOP				NOP					CLR A			MOV ALL,MC3			;
	MVI PWRTE,PL															;
	ADD				NOP					MOV ALU,A		NOP					; CT3 = 63. Place origin DMA READ address at RAM3 62.
	SL				NOP					MOV ALU,A		NOP					;	
	NOP				NOP					NOP				MOV ALL,WA0			;
	NOP				NOP					CLR A			MOV ALL,MC3			; CT3 = ??. Place origin DMA WRITE address at RAM3 63 [end].
	;------------------------------------------------------------------------ MATH DATA TRANSFER

	;------------------------------------------------------------------------
	NOP				NOP					NOP				MOV 0,CT0			; CT0 = 0.
	NOP				NOP					NOP				MOV 0,CT1			; CT1 = 0.
	NOP				NOP					NOP				MOV 0,CT2			; CT2 = 0.
	NOP				NOP					NOP				MOV 0,CT3			; CT3 = 0.
	;------------------------------------------------------------------------ Begin expanded bus.
	;	Flags: S for sign flag. A negative result of a logical operator [AND,OR,XOR] -OR- any arithmetic operator makes the sign flag 1.
	;	Flags: Z for zero flag. A zero result of a logical operator [AND,OR,XOR] -OR- any arithmetic operator makes the zero flag 1.
	;	Flags: C for carry flag. This is not a logical flag.
	;   IF SIGNS ARE DIFFERENT... "xor" operator of the two numbers is negative. S flag is 1. Else S flag is 0. jmp S
	;	IF TWO NUMBERS ARE EQUAL... subtract the two numbers. If they are equal, Z flag is 1. Else Z flag is 0. jmp Z
	;	IF A NUMBER IS NEGATIVE... a clear A and an AD2 command with the value in P will make the S flag 1. jmp S
	;	IF X <= Y ... subtract Y by X. If X == Y, Z flag is 1, jump! jmp Z. If X != Y, perform OR operator now. If S flag is 0, jmp NS.
	;	Alternatively, you can just subtract Y by X and check the sign flag after an OR operator on the result.
	;	IF X < Y ... subtract Y by X.  If they are equal, Z flag is 1, hitherto X == Y. Do not jump!
	;	To then assure that X < Y if we know that X != Y [Z flag is 0], perform "or" operator on result. If X < Y and X != Y, S flag is 0 and Z flag is 0. jmp NZS.
	;	TO NEGATE A [positive] NUMBER ... Move # to RX and -1 to RY. Mov mul P CLR A, ad2 over to A, mov ALL to RAM bank.
	;	Conditional statements need a "nop" after the jump, because the DSP pre-fetches instructions :)
	;	Subroutine \ Function execution: Place functions after main program "END". Move 1 to "LOP". Move the function label to the PC counter. Ensure a "nop" is after that command.
	;	Ensure functions end with "BTM" command. Rather than try to explain how that works, I'm just gonna say that it does.
	; Attempt division
	
	DVE = 649		; Initial dividend
	DVI = 49		; Initial divisor
					; Expression: DVE / DVI
	MVI DVE,MC0		; Dividend = RAM0 0
	MVI DVI,MC0		; Divisor = RAM0 1
	mov 0,ct0
	mov 0,ct1
	mov 0,ct3
	mvi 1,LOP
	mvi DIVIDE,PC
	nop
	END
	;-------------------------------------------------------------------------------------------------------------------------
	; Unsigned math only
	;-------------------------------------------------------------------------------------------------------------------------
	;	FUNCTION DIVIDE
	;
	;	INPUT
	;	Dividend ->			RAM0 0
	;	Divisor ->			RAM0 1
	;
	;	OUTPUT
	;	quotient ->			RAM1 1
	;
    ;	unsigned int tempdividend;
    ;	unsigned int tempdivisor;
	;	unsigned int tempquotient = 1;
	;	
	;	DATA
	;	tempdividend -> 	RAM0 2
	;	tempdivisor ->		RAM0 3
	;	tempquotient ->		RAM1 0
	;-------------------------------------------------------------------------------------------------------------------------
	DIVIDE:
					mov mc0,p 									clr a			mov 0,ct1 						;ct0 = 1
	ad2  			mov mc0,p 									mov alu,a		mov 1,mc1						;ct0 = 2 Store temporary quotient of 1 at RAM1 0
																clr a 			mov all,mc0						;ct0 = 3 Store copy of dividend at RAM0 2
	ad2 														mov alu,a										;
																clr a 			mov all,mc0						;ct0 = 4 Store copy of divisor at RAM0 3
	;-------------------------------------------------------------------------------------------------------------------------
    ;	if (tempdivisor >= tempdividend) {
	;		if(tempdivisor > tempdividend) tempquotient = 0;
	;		goto divend;
    ;	}
	;
	;	DATA
	;	tempdividend ->		RAM0 2
	;	tempdivisor ->		RAM0 3
	;	tempquotient ->		RAM1 0
	;-------------------------------------------------------------------------------------------------------------------------
																				mov 2,ct0						;ct0 = 2
					mov mc0,p									clr a 											;ct0 = 3
	ad2				mov mc0,p 									mov alu,a		mov 0,ct1						;ct0 = 4
	sub 														clr a			mov 3,ct0
	jmp ZS,DIVEND
	mvi 0,mc1,s	; Remember, the DSP caches instructions. Therefore, this instruction gets run even if we jump.
	;-------------------------------------------------------------------------------------------------------------------------
    ;	while (tempdivisor<<1 <= tempdividend)
    ;	{
    ;		tempdivisor = tempdivisor << 1;
    ;		tempquotient = tempquotient << 1;
    ;	}
	;
	;	DATA
	;	tempdividend ->		RAM0 2
	;	tempdivisor ->		RAM0 3
	;	tempquotient ->		RAN1 0
	;-------------------------------------------------------------------------------------------------------------------------
	jmp SLCOND:
	SLLOOP:
					mov m0,p									clr a 			mov 0,ct1						 ; CT0 = 3
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
																clr a			mov 3,ct0	;Prepares CT0 for next function segment
	;-------------------------------------------------------------------------------------------------------------------------
	;    // Call division recursively
	;		quotient += tempquotient;
    ;	    tempquotient = division(tempdividend-tempdivisor, divisor);
	;		
	;	DATA
	;	dividend ->		RAM0 0
	;	divisor ->		RAM0 1
	;	tempdividend -> RAM0 2
	;	tempdivisor	->	RAM0 3
	;	tempquotient->	RAM1 0
	;	quotient ->		RAM1 1
	;
	;	FUNCTION
	;	division 	-> label "DIVIDE"	
	;	Write:
	;	(tempdividend-tempdivisor) to RAM0 0
	;
	;-------------------------------------------------------------------------------------------------------------------------
					mov mc1,p
	ad2				mov mc1,p									mov alu,a
	ad2															mov alu,a		mov 1,ct1
																clr a			mov all,mc1 					; Move current quotient result added to previous quotient result to RAM1 1.
																clr a			mov 2,ct0
					mov mc0,p													mov 0,ct1
	ad2				mov mc0,p									mov alu,a										;
	sub															mov alu,a		mov 0,ct0
																				mov all,mc0
	jmp DIVIDE:
																				mov 0,ct0						;
	;-------------------------------------------------------------------------------------------------------------------------
	;	return tempquotient+quotient;
	;
	;	DATA
	;	tempquotient->	RAM1 0
	;	quotient ->		RAM1 1
	;	RETURN ->		RAM1 1
	;-------------------------------------------------------------------------------------------------------------------------
	DIVEND:																		mov 0,ct1
	mov mc1,p													clr a
	ad2				mov mc1,p									mov alu,a		mov 0,ct0						; Return used RAM bank to zero (no results here)
	ad2															mov alu,a		mov 1,ct1
																clr a			mov all,mc1
																				mov 1,ct1						; Return used RAM bank to result
	DMA mc1,D0,3
	BTM
	
	