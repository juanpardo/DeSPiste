	PREAD = 12584960	; Constant to be changed by SH2 before program load.
	WRITE = 12584960	; Constant to be changed by SH2 before program load.
	NOTI = 12584960	;
	;------------------------------------------------------------------------ P64 PROGRAM DMA HEADER
	MVI WRITE,PL															; SH2 sets "PREAD" and "WRITE" constants before program load.
	ADD				NOP					MOV ALU,A		MOV 62,CT3			; MVI is 25-bit signed data. So it requires 3 shifts right to get high memory address in that bit depth.
	SL				NOP					MOV ALU,A		MOV 0,CT0			; As DSP reads data in DWORD units, the address actually must be on 4-byte boundaries,
	NOP				NOP					NOP				MOV ALL,WA0			; so we need to shift left one to get the proper address in RA0 and WA0.
	NOP				NOP					CLR A			MOV ALL,MC3			;
	MVI PREAD,PL															;
	ADD				NOP					MOV ALU,A		MOV 0,CT2			; CT3 = 63. Place origin DMA WRITE address at RAM3 62.
	SL				NOP					MOV ALU,A		MOV 0,CT1			;	
	NOP				NOP					NOP				MOV ALL,RA0			;
	NOP				NOP					CLR A			MOV ALL,MC3			; CT3 = ??. Place origin DMA READ address at RAM3 63 [end].
	MVI NOTI,PL																;
	ADD									mov alu,a		mov 59,ct3			;
	sl									mov alu,a							;
										clr a			mov all,mc3			; Place program end notification address at RAM3 59
	;-----------------------------------------------------------------------------------------------------------------------
	;	What this program does:
	;	DMA's in a loop control value from high memory to tell it how many times to iterate,
	;	Takes 8-bit Y value data for a polygon from high memory compressed into a single 32-bit value,
	;	DMA's it in,
	;	and decants it into 4 fixed-point values, each bound at byte 15.
	;	It then calculates the normal of this polygon as if the X and Z values of each vertice were something like 25<<16 +X/-Z : +x / +z : +x / -z : -x / -z
	;	Then it binds the output normal to bit 9.
	;	Then it finds the sign of the X and Z components of the normal. Y component is always positive.
	;	It writes sign bits for X and Z to bits 30 and 31 of the output. Bit 30 is the sign bit for X and bit 31 is the sign bit for Z.
	;	It then concantenates the values into a single 32-bit number, 10 bits each, with X from 0-9, Y from 10-19, and Z from 20-29.
	;	That value is DMA'd out to high memory.
	;	Then, it repeats, adding 1 to the read and write address, until the loop count meets the loop control value.
	;	Then it DMA's out the decimal number "40" to the notification of end status address.
	;-----------------------------------------------------------------------------------------------------------------------
	; Initialization
	; DMA IN a loop count number. Then add 1 to the read address, because we don't want to store a different address, but the data we want to read is after this data.
	;	DATA
	;		Notification Addr	->		RAM3 59 [Noti End Addr to write to]
	;		Loop Control		->		RAM3 60 [Number of loops desired]
	;		Loop Count			->		RAM3 61 [Number of loops run]
	;		Write address		->		RAM3 62
	;		Read address		->		RAM3 63
	;		Input Data Target	->		RAM1 7
	;-----------------------------------------------------------------------------------------------------------------------
	dma d0,mc3,1														; CT3 = 60
														mov 0,mc3		; CT3 = 61 ; DMA in loop control number
														mov 63,ct3		; CT3 = 62 ; Zero out the loop count number [ leftover from previous frames ]
										mov m3,a		mov 1,PL		; CT3 = 63 ; Pass over write address to read address
	add									mov alu,a		mov 7,ct1		;
														mov all,ra0		; Add 1 to read address
										clr a			mov all,mc3		; Store the read address
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 0 ; CT1 = 7 ; CT2 = 0 ; CT3 = 0 ; A = Clear
	; Part 0 DMA in 32-byte compressed polygon; 8 bytes per vertice, only the Y value of each vertice.
	;-----------------------------------------------------------------------------------------------------------------------
FOR_NORM:												
	dma	d0,mc1,1
	;-----------------------------------------------------------------------------------------------------------------------
	; Part 1: Decompress Y values stored in RAM1 7 out to RAM0 0,1,2,3 as being shfited left 16 times (mul by 65536).
	;-----------------------------------------------------------------------------------------------------------------------
	NOP				NOP					clr a			MOV 7,CT1			;
										mov m1,a		mov 0,ct0			; 
	mvi 16711680,PL															; CT0 = 0 ; 
	and				nop					mov alu,a						; MVI Bitmask to P ;						
										clr a			mov ALL,mc0			; 
										mov m1,a							; CT0 = 1 ; Shifts Y value 2 from bits 16-23 to bits 8-15. 
	mvi 255,PL							
	and				nop					mov alu,a		mov 15,LOP			; MVI Bitmask to P
	lps																		;
	sl									mov alu,a							;
										clr a			mov ALL,mc0			; Shifts Y value 0 from bits 0-7 to bi v ts 8-15.
	mvi 65536,RX
	mvi 65280,PL															; Mask Shifter to X
	ad2									mov alu,a		mov 8,ct1			; Mask Starter to P
														mov all,mc1			; Move PL to A [since A is zero, adding just moves it]
														mov 8,ct1			; CT1 = 9 ; Temp data to RAM1 8
										mov m1,y		mov 7,ct1			; CT1 = 8
					mov mul,p			mov m1,a		mov 0,ct2			; CT1 = 7
	and				nop					mov alu,a		mov 2,LOP			; Ultimate bitmask is in P
	lps																		; PROBLEM: Shifting this masked value right will drag the sign bit over.
	rl8									mov alu,a							; Instead, let's rotate it right.
										clr a			mov ALL,mc0			; Shifts Y value 3 from bits 24-32 to bits 8-15.
	mvi 65280,PL															; CT0 = 3 ;
										mov m1,a		mov 0,ct1 			; MVI Bitmask for Y value 1 to P
	and									mov alu,a		mov 7,LOP			; Move comp data to A
	
	lps
	sl									mov alu,a		mov 0,ct3
										clr a			mov ALL,mc0			; Mask bits 8-15
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 4 ; CT1 = 0 ; CT2 = 0 ; CT3 = 0 ; Y value 1 in RAM0 3.
	;-----------------------------------------------------------------------------------------------------------------------
	jmp CALCNORM:															;Jump to function that calculates normal from Y values read in to RAM0 0123
	RTNORM:
	nop									clr a			mov 0,ct0			; (will be executed before the jump and after the jump)
	;-----------------------------------------------------------------------------------------------------------------------
	; Part 4: Shift each normal component [X,Y,Z] right, six times, and then concantenate the result into a single RAM address.
	; The normal components are in RAM2 0,1,2 as X, Y, Z.
	; CT0 = 0 ; CT1 = 0 ; CT2 = 0 ; CT3 = 0 ; 
	;
	;	DATA
	;	IN	Calculated Polygon Normal 		->		RAM2 0,1,2 as X,Y,Z
	;	OUT	Compressed Component Data		->		RAM2 0,1,2 as X,Y,Z
	;-----------------------------------------------------------------------------------------------------------------------
										mov m2,a		mov 5,LOP	;CT2 = 0
	lps																;IN: Calc X Value
	sr									mov alu,a		mov 0,ct0
										clr a			mov all,mc2
										mov m2,a		mov 5,LOP	;CT2 = 1 ; OUT: Shifted X Value
	lps																;IN: Calc Y Value
	sr									mov alu,a		mov 0,ct1
										clr a			mov all,mc2 ;
										mov m2,a		mov 5,LOP	;CT2 = 2 ; OUT: Shifted Y Value
	lps																;IN: Calc Z Value
	sr									mov alu,a		mov 0,ct3
										clr a			mov all,mc2
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 0 ; CT1 = 0 ; CT2 = 3 ; CT3 = 0 ; A: Clear 
	;	PROBLEM: The sign bit is destroyed.
	;	Logic must be added to preserve the sign of each normal component.
	;	The input Y values are always positive, no worries about them, but the outputs are signed.
	;	Another issue is the sign of the data destroys its ability to be uniformly condensed into 4 bytes.
	;	Instead of 10 bits for each component, we could apply a more universal approach...
	;	Bits 29, 30, and 31 are sign bits for components X, Y, and Z, respectively.
	;	X and Z will preserve their 10-byte depth.
	;	Y will be reduced to 9 bit depth.
	;	But given our code structure, Y has an assumed sign. Only X and Z vary.
	;	In this case, bits 30 and 31 can be sign bits for X and Z. Y is always positive.
	;-----------------------------------------------------------------------------------------------------------------------
														mov 3,ct2
														mov 0,mc2	
														mov 0,ct2	; This sequence zeroes out the comp data in RAM2 3; if we skip -X, it's possible that -Z will blindly read it.
					mov m2,p										; CT2 = 0
	ad2									mov alu,a					;
	jmp NS,SKXN
	mvi -1,PL														; What follows is the path taken if X is negative.
	add									mov alu,a		mov 3,ct2	; Goal: Ensure X is positive. Write 1 to bit 30, this sign bit, of RAM2 3.
	xor									mov alu,a		mov 1,mc2	; CT2 = 3 ; Add -1 to the negative number to compensate for inversion loss ; Select comp data's home
														mov 0,ct2	; CT2 = 4 ; XOR to invert ; Move 1 to the comp data's home
										clr a			mov all,mc2	; CT2 = 0 ; Select shifted X data's home
	SKXN: 								clr a			mov 2,ct2	; CT2 = 1 ; Move inverted to positive X back to its RAM place. ; Skip X Negative Tagline
					mov m2,p										; CT2 = 2
	ad2									mov alu,a					; 
	jmp NS,SKZN														;
	mvi -1,PL														; What follows is the path taken if Z is negative.
	add									mov alu,a					;
	xor									mov alu,a					; Add -1 to the negative number to compensate for inversion loss
										clr a			mov all,mc2	; XOR to ivnert
										mov m2,a		mov 2,PL	; CT2 = 3 ; Move inverted positive Z back to its RAM place
	add									mov alu,a					; Move the sign mask to A and 2 to PL
										clr a			mov all,mc2	; Add 2 to the sign mask ; if +X, it's now 01. If -X, it's now 11.
	SKZN:												mov 3,ct2	; CT2 = 4
										mov m2,a		mov 0,ct2	; CT2 = 3
	rr									mov alu,a
	rr									mov alu,a					; Condition after this instruction is that if -X / -Z, bits 30 and 31 will be high, and low if not.
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 0 ; CT1 = 0 ; CT2 = 0 ; CT3 = 0 ;
	; Our compression goal is X being from bits 0-9, Y being from bits 10-19, and Z being from bits 20-29. 30 is blank and 31 is the sign bit.
	;
	;	DATA
	;	IN	Compressed Component Data		->		RAM2 0,1,2 as X,Y,Z
	;	OUT	Compressed Single 4-byte		->		RAM2 3
	;-----------------------------------------------------------------------------------------------------------------------
										mov mc2,y		mov 1,RX	;CT2 = 0
					mov mul,p
	or									mov alu,a
	mvi 1024,RX														;CT2 = 1
										mov mc2,y					; MVI 10-bit Shifter to RX
					mov mul,p										;CT2 = 2 ; Move shifted Y to.. RY
	or									mov alu,a					; Multiply to shift that back left, 10 times
	mvi 1048576,RX													; OR operation combines it with compressed X data
										mov mc2,y					; MVI 20-bit shifter to RX
					mov mul,p										;CT2 = 3 ; Move shifted Z to RY
	or									mov alu,a		mov 60,ct3	; Multiply to shift Z left 20 times
										clr a			mov all,mc2 ; Combine Z in bits 20-29 with Y in bits 10-19 and X in bits 0-9.
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 0 ; CT1 = 0 ; CT2 = 4 ; CT3 = 60 ;
	; Loop count + read address should be the correct address, in RA0 now.
	; Part 6: If subtracting the loop control number by the loop count value is zero or negative, jump to program end. Otherwise, jump to part 0.				
	;
	; DATA
	;		Loop Control 	->		RAM3 60
	;		Loop Count		->		RAM3 61
	;-----------------------------------------------------------------------------------------------------------------------	
										mov mc3,a
					mov mc3,p										; CT3 = 61
	sub									clr a			mov 0,ct3	; CT3 = 62
	jmp ZS,PRGEND													; CT3 = 0 ; Perform Loop Control - Loop Count
	nop													mov 61,ct3	; If the Z or S flag are up (if subtraction was negative or zero), jump to PRGEND.
	;-----------------------------------------------------------------------------------------------------------------------
	; CT0 = 0 ; CT1 = 0 ; CT2 = 4 ; CT3 = 61 ;
	; Part 5: DMA out the compressed normal. Increment write address. Increment read address. Add to a loop count value. 
	;
	;	DATA
	;	IN
	;		Compressed norm	->		RAM2 3
	;		Loop count		->		RAM3 61
	;		Write address	->		RAM3 62
	;		Y-value addr	->		RAM3 63
	;	OUT
	;		Comp norm to..	->		Write addr [WA0]
	;		Loop count +1	->		RAM3 61
	;-----------------------------------------------------------------------------------------------------------------------
										mov m3,a		mov 1,PL	;
	ad2									mov alu,a		mov 3,ct2	; Move loop count to A and 1 to PL
										clr a			mov all,mc3 ; CT2 = 3 ; Add 1 to loop count
	dma mc2,d0,1													; CT3 = 62 ; Move added loop count back to RAM3 61
										mov m3,a		mov 1,PL	; DMA Out Complete
	ad2									mov alu,a					; Move Write Addr to A and 1 to PL 
														mov all,mc3 ; Add 1 to write addr
										clr a			mov all,wa0 ; CT3 = 63 ; Move Write Addr Back Out	
										mov m3,a		mov 1,PL	; Move Write Addr to WA0
	ad2									mov alu,a					; Move Read Addr to A and 1 to PL
														mov all,mc3 ; Add 1 to read addr
										clr a			mov all,ra0	; CT3 = 0 ; Move read addr back out
	jmp FOR_NORM													; Move Read Addr to RA0
	nop													mov 7,ct1	; Return to process next polygon data
	PRGEND:															;
														mov 59,ct3
														mov mc3,wa0
														mov 0,ct0
														mov 40,mc0
														mov 0,ct0
	dma mc0,d0,1
	ENDI
	nop									clr a
;As far as I know, I have 116 instructions for the body.
;Said body is part 0, part 1, part4, part5, and part 6.

;Why make this effort?
; 1 - It just uses the DSP for *something*.
; 2 - Let's consider the cache access that the SH2 has to do for a normal.
; It's about 15x4 bytes per normal. The typical normal amount is 24, so that's 1440 bytes.
; Sometimes its 48, which is 2880 bytes.
; If the DSP did this, it accesses high memory 24 or 48 times to read the data in. [96 or 192 bytes]
; Then it accesses high memory 24 or 48 times to get the data out [96 or 192 bytes]
; Then the SH2 accesses memory 48x6 times to decompress the data, assuming it works out like that.
; The important part is, over 2 KB of SH2 cache is saved.

; Complications:
; At least 576x4 bytes must be used for the compressed data ready area. Incidentally, that array is already in memory.
; At least 576x4 bytes must be used for the compressed data output area.
; Just scale both up to 580, for safety.
; 2320x2 buffers, so about 4KB ish of high memory is eaten.
; Tolerable.

	;-----------------------------------------------------------------------------------------------------------------------
	;	FUNCTION SEGMENT
	;		rminusb and sminusd
	;
	;	rminusb[X] = -25<<16
	;	rminusb[Y] = sample2[Y] - sample0[Y];
	;	rminusb[Z] = 25<<16
	;
	;	sminusd[X] = 25<<16
	;	sminusd[Y] = sample3[Y] - sample1[Y];
	;	sminusd[Z] = 25<<16
	;
	;	DATA
	;		sample 0,1,2,3 -> in RAM0 in order of 2Y0Y, 3Y1Y.
	;												01	23
	;		From RAM0 0 to RAM0 11.
	;
	;		rminusb		-> in RAM1 0-2 in order as X,Y,Z
	;		sminusd		-> in RAM2 0-2 in order as X,Y,Z
	;
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 0
	;	rminusb[X] = -25<<16
	;	rminusb[Y] = sample2[Y] - sample0[Y];
	;	rminusb[Z] = 25<<16
	;-----------------------------------------------------------------------------------------------------------------------
	;ALU			X-bus X		X-Bus P				Y-Bus Y		Y-bus A			D1-bus			; 
	CALCNORM:
	mvi -1638400,MC1
					mov mc0,p															
	ad2				mov mc0,p	nop					nop			mov alu,a		nop				;
	sub				nop			nop					nop			mov alu,a		nop				;
	NOP				NOP			NOP					NOP			clr a			mov all,mc1		;
	mvi 1638400,MC1
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 4,	CT1 = 3,	CT2 = 0,	CT3 = 0
	;	sminusd[X] = 25<<16
	;	sminusd[Y] = sample3[Y] - sample1[Y];
	;	sminusd[Z] = 25<<16
	;-----------------------------------------------------------------------------------------------------------------------
	mvi 1638400,MC2
					mov mc0,p															
	ad2				mov mc0,p	nop					nop			mov alu,a		mov 0,ct0		;
	sub				nop			nop					nop			mov alu,a		mov 1,ct1		;
	NOP				NOP			NOP					NOP			clr a			mov all,mc2		;
	mvi 1638400,MC2
																				mov 2,ct2		;
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 1,	CT2 = 2,	CT3 = 0
	;	FUNCTION SEGMENT
	;	Cross-product
	;
	;	 output[X] = slMulFX(rminusb[Y], sminusd[Z]) - slMulFX(rminusb[Z], sminusd[Y]);
	;	 output[Y] = slMulFX(rminusb[Z], sminusd[X]) - slMulFX(rminusb[X], sminusd[Z]);
	;	 output[Z] = slMulFX(rminusb[X], sminusd[Y]) - slMulFX(rminusb[Y], sminusd[X]);
	;
	;	DATA
	;		rminusb	->	RAM1 0,1,2
	;		sminusd	->	RAM2 0,1,2
	;		output	->	RAM2 0,1,2
	;	TEMPORARY DATA
	;		High-order bits of 32bit x 32bit -> RAM0 0,1,2,3,4,5
	;
	;-----------------------------------------------------------------------------------------------------------------------
	;slMulFX(rminusb[Y], sminusd[Z])	->	RAM0 0
	;-----------------------------------------------------------------------------------------------------------------------
	MOV M1,X		MOV M2,Y											;
	MOV MUL,P					mov 2,ct1								;	RAM0 will be used as a temporary location for the high-order bits of the cross product multiplication.
	ad2				mov alu,a	mov 1,ct2								;	Cross product outputs to RAM3 0-2 as X,Y,Z.
					clr a		mov alh,mc0								;
	;-----------------------------------------------------------------------------------------------------------------------
	;slMulFX(rminusb[Z], sminusd[Y])	->	RAM0 1
	;-----------------------------------------------------------------------------------------------------------------------
	mov m1,x		mov m2,y
	mov mul,p					mov 0,ct1
	ad2				mov alu,a	mov 1,ct2
					clr a		mov alh,mc0
	;-----------------------------------------------------------------------------------------------------------------------
	;slMulFX(rminusb[X], sminusd[Y])	->	RAM0 2
	;-----------------------------------------------------------------------------------------------------------------------
	mov m1,x		mov m2,y	
	mov mul,p					mov 1,ct1
	ad2				mov alu,a	mov 0,ct2
					clr a		mov alh,mc0
	;-----------------------------------------------------------------------------------------------------------------------
	;slMulFX(rminusb[Y], sminusd[X])	->	RAM0 3
	;-----------------------------------------------------------------------------------------------------------------------
	mov m1,x		mov m2,y	
	mov mul,p					mov 0,ct1
	ad2				mov alu,a	mov 0,ct2
					clr a		mov alh,mc0
								mov 0,ct0
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 0
	;	Multiplication done, time for subtraction and output.
	;-----------------------------------------------------------------------------------------------------------------------
	;	 output[X] = slMulFX(rminusb[Y], sminusd[Z]) - slMulFX(rminusb[Z], sminusd[Y])>>8	->	RAM3 0
	;-----------------------------------------------------------------------------------------------------------------------
		mov mc0,p
	ad2	mov mc0,p	mov alu,a	
	sub				mov alu,a
	mvi 7,LOP
	LPS
	sr				mov alu,a			; Shifting right to suppress overflows (in normalization)
					clr a		mov all,mc3
	;-----------------------------------------------------------------------------------------------------------------------
	;	 output[Y] = slMulFX(rminusb[Z], sminusd[X]) - slMulFX(rminusb[X], sminusd[Z])>>8	->	RAM3 1	;	This is a known constant...
	;-----------------------------------------------------------------------------------------------------------------------
	mvi 320000,mc3
	;-----------------------------------------------------------------------------------------------------------------------
	;	 output[Z] = slMulFX(rminusb[X], sminusd[Y]) - slMulFX(rminusb[Y], sminusd[X])>>8	->	RAM3 2
	;-----------------------------------------------------------------------------------------------------------------------
		mov mc0,p
	ad2	mov mc0,p	mov alu,a	
	sub				mov alu,a
	mvi 7,LOP
	LPS
	sr				mov alu,a			; Shifting right to suppress overflows
					clr a		mov all,mc3
	MOV 0,CT3							; CT0 = 0
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 0
	;	FUNCTION
	;		Normalize (Fixed Point)
	;	INPUTS
	;		Cross-Product Vector
	;	OUTPUTS
	;		Normalized Vector
	;	SUB-FUNCTION
	;		Inverse Square Root
	;	BODY
	; 	static FIXED isqrt = 0;
	; 	isqrt = fxisqrt(slMulFX(cross[X],cross[X]) + slMulFX(cross[Y],cross[Y]) + slMulFX(cross[Z],cross[Z]));
	; 	normal[X] = slMulFX(isqrt, cross[X]);
	; 	normal[Y] = slMulFX(isqrt, cross[Y]);
	;	normal[Z] = slMulFX(isqrt, cross[Z]);
	;
	;	DATA
	;		isqrt 	->	RAM1 1
	;		cross	->	RAM3 0,1,2
	;-----------------------------------------------------------------------------------------------------------------------
	;	slMulFX(cross[X],cross[X]) + slMulFX(cross[Y],cross[Y]) + slMulFX(cross[Z],cross[Z])
	;		TEMPORARY DATA
	;	Square Magnitude	-> "SM"
	;		SM				->	RAM3 3
	;-----------------------------------------------------------------------------------------------------------------------
	mov m3,x		mov m3,y	
	mov mul,p								mov 1,ct3
	ad2	mov m3,x	mov m3,y	mov alu,a	; X*X
	mov mul,p								mov 2,ct3
	ad2	mov m3,x	mov m3,y	mov alu,a	; Y*Y + X*X
	mov mul,p								mov 3,ct3
	ad2							mov alu,a	; Z*Z + Y*Y + X*X
											mov alh,mc3
											mov 3,ct3
	;-----------------------------------------------------------------------------------------------------------------------
	;	FUNCTION
	;		Inverse Square Root [Fixed Point]
	;	INPUTS
	;		Square Magnitude -> "SM"
	;	OUTPUTS
	;		Approximately 1/sqrt(SM) -> "isqrt"
	;	BODY
	;		xSR = 0;
	;		pushRight = SM;
	;		msb = 0;
	;		shoffset = 0;
	;		yIsqr = 0;
	;											; We will be doing something different...
	;		while(pushRight >= 65536){			; While carry flag is 0
	;			pushRight >>=1;					; Shift LEFT.
	;			msb++;							; place++;
	;		}									; This kind of logic has no real equivalency in C since it is dependent on register logic flags.
	;											; msb = 16 - place;
	;		shoffset = (16 - ((msb)>>1));
	;		yIsqr = 1<<shoffset;
	;		xSR = SM>>1;
	;		return (slMulFX(yIsqr, (98304 - slMulFX(xSR, slMulFX(yIsqr, yIsqr)))));
	;
	;	DATA
	;		SM 			->		RAM3 03
	;		xSR			->		RAM0 0
	;		pushRight	->		Temporary in RAM0 1
	;		msb/place	-> 		Temporary in RAM0 0
	;		shoffset	->		Calculated, then used as loop counter (goes to LOP)
	;		yIsqr		->		RAM1 0
	;		Return		->		RAM1 1
	;		
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 3
	;											; We will be doing something different...
	;		while(pushRight >= 65536){			; While carry flag is 0
	;			pushRight >>=1;					; Shift LEFT.
	;			msb++;							; place++;
	;		}									; This kind of logic has no real equivalency in C since it is dependent on register logic flags.
	;-----------------------------------------------------------------------------------------------------------------------
					mov m3,a		mov 1,ct0
	sl				mov alu,a						; Shift Square Magnitude left once
						clr a		mov all,mc0		;ct0 = 2 ; Move SM<<1 out as pushRight
									mov 0,ct0		;ct0 = 0
	jmp	PUSHLCOND:
					mvi 1,mc0		;ct0 = 1		; The initial condition, as pushRight has already been shifted once, is that MSB is 1.
	PUSHLEFT:
					mov m0,a		mov 1,PL
	ad2				mov alu,a					; Add 1 to msb
					clr a			mov all,mc0	; ct0 = 1
					mov m0,a
	sl				mov alu,a					; Shift pushRight left once
					clr a			mov all,mc0	; ct0 = 2
	PUSHLCOND:
	jmp NC,PUSHLEFT:
					clr a			mov 0,ct0				;(this instruction is part of the loop)
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 3
	;		msb = 17* - place;
	;		shoffset = (16 - ((msb)>>1));
	;		yIsqr = 1<<shoffset;
	;		xSR = SM>>1;
	;
	;	DATA
	;		msb/place 	->	RAM0 0
	;		shoffset 	->	goes to LOP
	;		yIsqr		->	RAM1 0
	;		xSR			->	RAM0 0
	;-----------------------------------------------------------------------------------------------------------------------
									mvi 17,PL				; perform 17 - place ; because our shifting output is 1 less than it should be.
	ad2	mov m0,p	mov alu,a								; select shoffset/msb/place in memory
	sub				mov alu,a								; Make MSB = 16 - place
	sr				mov alu,a		mov 16,PL				; now shift right, as MSB>>1 ; and prepare to do 16 - MSB>>1
					clr a			mov all,mc0				; ct0 = 2
	ad2				mov alu,a		mov 0,ct0				; Re-select MSB
		mov m0,p											;
	sub				mov alu,a		mov 1,PL				; We need to start moving 1 to A to shift it. ; This line also makes shoffset = 16 - (msb>>1) ;
					clr a			mov all,LOP				; shoffset is just a loop counter, so it needs not be moved out to memory.
	ad2				mov alu,a								; This line modes 1 from P to A.
	LPS														;
	sl				mov alu,a		mov 0,ct0				; This makes yIsqr, the initial guess.
	sr				mov alu,a								; There's a shift right here to get it to where we want it as the loop runs once more than the loop counter.
		mov m3,p	clr a			mov all,mc1				; ct1 = 1 ; Now it is time to make xSR and store it in RAM0 0, source data RAM3 3.
	ad2				mov alu,a		mov 0,ct1				; Re-select yIsqr
	sr				mov alu,a								;
					clr a			mov all,mc0				; ct0 = 1
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 1,	CT1 = 0,	CT2 = 0,	CT3 = 3
	;	(slMulFX(yIsqr, (98304 - slMulFX(xSR, slMulFX(yIsqr, yIsqr)))));
	;	BREAKDOWN
	;	slMulFX(yIsqr, yIsqr) -> Stored at RAM0 2
	;
	;	DATA
	;		yIsqr		->		RAM1 0
	;		xSR			->		RAM0 0
	;		98304		->		Immediate Data
	;-----------------------------------------------------------------------------------------------------------------------
		mov m1,x	mov m1,y				mov 0,ct0		; select xSR ; yIsqr^2
		mov mul,p											;
	ad2				mov alu,a								;
					mov m0,y	clr a		mov alh,RX		; yIsqr^2 * xSR
		mov mul,p											;
	ad2				mov alu,a				mov 2,ct0		;
					clr a					mov alh,mc0		; temporary storage location in ram0 2
											mvi 98304,PL	;
	ad2				mov alu,a				mov 2,ct0		;
		mov m0,p											;
	sub				mov alu,a								;
					mov m1,y	clr a		mov all,RX		; yIsqr * (98304 - result)
		mov mul,p							mov 0,ct3		;
	ad2				mov alu,a				mov 0,ct0		;
											mov alh,mc1		;
						clr a				mov alh,RX		;
											mov 0,ct1		;
	;-----------------------------------------------------------------------------------------------------------------------
	;	CT0 = 0,	CT1 = 0,	CT2 = 0,	CT3 = 0
	; That's the end of inverse sqrt. The output is in RAM1 1. And, in this demo program, the isqrt is in RX.
	;-----------------------------------------------------------------------------------------------------------------------
	; 	normal[X] = slMulFX(isqrt, cross[X]);
	; 	normal[Y] = slMulFX(isqrt, cross[Y]);
	;	normal[Z] = slMulFX(isqrt, cross[Z]);
	;
	;	DATA
	;		isqrt			->				RAM1 1 / RX
	;		cross			->				RAM3 0,1,2
	;		normal			->				RAM2 0,1,2
	;-----------------------------------------------------------------------------------------------------------------------
	; Inverse sqrt * cross product X
	; Output in RAM2 0-2
	;-----------------------------------------------------------------------------------------------------------------------
					mov mc3,y								; 
		mov mul,p	mov mc3,y								;
	ad2	mov mul,p	mov mc3,y 	mov alu,a					;
					clr a					mov alh,mc2				
	ad2	mov mul,p	mov alu,a		
					clr a					mov alh,mc2
	ad2				mov alu,a
					clr a					mov alh,mc2
	;-----------------------------------------------------------------------------------------------------------------------
	; Re-select the base of RAM2 to DMA the result out.
	;-----------------------------------------------------------------------------------------------------------------------
	jmp RTNORM:
	nop										mov 0,ct2
	
