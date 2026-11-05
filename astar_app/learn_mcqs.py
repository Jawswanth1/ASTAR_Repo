"""Checked MCQ adaptations of prompts in the uploaded Ganita Prakash chapter."""
def ganita_mcqs():
    bank=[]
    def add(page,prompt,choices,answer,why,hint=None):
        bank.append(dict(id=f'gp-mcq-{len(bank)+1}',page=page,printedPage=page,label=f'Textbook practice · {len(bank)+1}',
          kind='mcq',prompt=prompt,text=prompt,choices=[str(c) for c in choices],answer=answer,explanation=why,
          hints=[hint or 'Return to the rule or example in this part of the chapter.',why],feedbackType='verified',
          origin='Textbook question adapted to MCQ · ASTAR choices',checklist=[]))
    add(1,'Which locker numbers remain open after all 100 people have taken their turns?',
        ['The prime numbers','The perfect squares','All even numbers','All odd numbers'],1,'Only perfect squares have an odd number of factors, so only they are toggled an odd number of times.','Pair the factors of a locker number.')
    add(2,'Does every number have an even number of factors?',['Yes','No'],1,'A perfect square has one repeated partner factor. For example, 4 has three factors: 1, 2 and 4.')
    add(2,'Does 36 have an odd number of factors?',['No: it has 6','Yes: it has 9','No: it has 8','Yes: it has 7'],1,'The factors are 1, 2, 3, 4, 6, 9, 12, 18 and 36: nine factors.')
    add(3,'Which are the first five lockers that are toggled exactly twice?',
        ['1, 4, 9, 16, 25','2, 4, 6, 8, 10','2, 3, 5, 7, 11','1, 2, 3, 4, 5'],2,'Numbers with exactly two positive factors are prime. The first five primes are 2, 3, 5, 7 and 11.')
    add(4,'If a number ends in 0, 1, 4, 5, 6 or 9, is it always a square?', ['Yes','No'],1,'No. For example, 26 ends in 6 but is not a perfect square.')
    for n in [6,7,8,9,12,13,14,15]:
        value=n*n;add(4,f'Complete the textbook square table: {n}² = ?', [value-2*n,value+n,value,value+1],2,f'{n} × {n} = {value}.','Multiply the number by itself.')
    add(5,'Which listed squares have 6 in the units place?',
        ['38² and 82²','34², 46², 56² and 74²','All six listed squares','Only 46²'],1,'Numbers ending in 4 or 6 have squares ending in 6.')
    add(5,'If a number contains exactly 3 zeros at the end, how many zeros will its square have at the end?',[3,6,9,12],1,'Squaring doubles the number of trailing zeros: (a × 1000)² = a² × 1000000.')
    add(5,'What can you say about the parity of a number and its square?', ['They have the same parity','They have opposite parity','Every square is odd','Every square is even'],0,'Even × even is even, and odd × odd is odd.')
    add(6,'Using the pattern, find 36², given that 35² = 1225.',[1226,1260,1296,1369],2,'36² = 35² + 2 × 35 + 1 = 1225 + 71 = 1296.')
    add(6,'What is the nth odd number?', ['n + 1','2n','2n − 1','n²'],2,'The sequence 1, 3, 5, … is given by 2n − 1.')
    add(7,'What is the largest square less than 1000?', [900,961,999,1024],1,'31² = 961 and 32² = 1024, so 961 is the largest below 1000.')
    add(7,'How many square numbers are there in the block 1–100?', [9,10,11,12],1,'The squares of 1 through 10 lie in this inclusive block.')
    add(7,'How many square numbers are there in the block 101–200?', [3,4,5,6],1,'11², 12², 13² and 14² are 121, 144, 169 and 196.')
    add(7,'The area of a square is 49 sq. cm. What is the length of its side?', ['7 cm','14 cm','24.5 cm','49 cm'],0,'7 × 7 = 49, so the side length is 7 cm.')
    add(8,'What is the positive square root of 64?', [6,8,16,32],1,'8 × 8 = 64. This question asks for the positive root.')
    for n,root in [(324,18),(156,None),(1156,34),(2800,None)]:
        add(9,f'Is {n} a perfect square?', ['Yes','No'],0 if root else 1,
            f'{root}² = {n}.' if root else f'{n} has prime factors that cannot all be paired.')
    add(10,'Which group contains the numbers that are NOT perfect squares?',
        ['2032, 2048 and 1027','Only 1089','2032 and 1089','All four numbers'],0,'2032, 2048 and 1027 have impossible units digits for squares. 1089 = 33².')
    add(10,'Given 125² = 15625, what is the value of 126²?',
        ['15625 + 126','15625 + 262','15625 + 253','15625 + 251'],3,'The difference is 2 × 125 + 1 = 251. Thus 126² = 15876.')
    add(10,'Find the length of the side of a square whose area is 441 m².', ['19 m','20 m','21 m','22 m'],2,'21 × 21 = 441.')
    add(10,'Find the smallest square number divisible by 4, 9 and 10.', [90,180,360,900],3,'The least common multiple is 180 = 2² × 3² × 5. Pair the remaining 5: 180 × 5 = 900.')
    add(10,'What is the smallest number by which 9408 must be multiplied to make a perfect square?', [2,3,6,7],1,'9408 = 2⁶ × 3 × 7². Multiplying by 3 pairs every prime factor; √28224 = 168.')
    for a in [16,99]:add(10,f'How many integers lie strictly between {a}² and {a+1}²?', [a,2*a,2*a+1,a*a],1,f'The difference between the squares is {2*a+1}; excluding the endpoints leaves {2*a} integers.')
    for n in [2,3]:add(11,f'How many cubes of side 1 cm make a cube of side {n} cm?', [n,n*n,n**3,n**3+1],2,f'There are {n} × {n} × {n} = {n**3} unit cubes.')
    add(12,'Is 9 a perfect cube?', ['Yes','No'],1,'2³ = 8 and 3³ = 27. Nine lies strictly between these consecutive cubes.')
    add(12,'How many unit cubes are in a cube with edge length 4 units?', [12,16,48,64],3,'There are 4 layers of 4 × 4 cubes, giving 64.')
    for n in [6,7,8,9,10,12,15,16,20]:
        value=n**3;add(12,f'Complete the textbook cube table: {n}³ = ?', [n*n,value-1,value,value+n],2,f'{n} × {n} × {n} = {value}.')
    add(13,'Can a perfect cube end with exactly two zeros?', ['Yes','No'],1,'The number of trailing zeros in an integer cube is a multiple of 3.')
    add(13,'Which two sums of positive cubes both equal 4104?',
        ['2³ + 16³ and 9³ + 15³','1³ + 12³ and 9³ + 10³','3³ + 16³ and 9³ + 14³','2³ + 15³ and 8³ + 16³'],0,'8 + 4096 = 4104 and 729 + 3375 = 4104.')
    add(14,'What is the sum 91 + 93 + 95 + … + 109?', [100,900,1000,1100],2,'There are 10 terms with mean 100, so the sum is 1000 = 10³.')
    add(14,'Is 3375 a perfect cube?', ['Yes: 15³','Yes: 25³','No','Yes: 35³'],0,'3375 = 3³ × 5³ = (3 × 5)³ = 15³.')
    add(14,'Is 500 a perfect cube?', ['Yes','No'],1,'500 = 2² × 5³. The two factors of 2 cannot form a triplet.')
    for n,root in [(64,4),(512,8),(729,9)]:add(15,f'Find the cube root of {n}.',[root-1,root,root+1,n//2],1,f'{root}³ = {n}.')
    for n,root in [(27000,30),(10648,22),(1331,11),(4913,17),(12167,23),(32768,32)]:
        add(16,f'Find the cube root of {n}.',[root-2,root-1,root,root+1],2,f'{root} × {root} × {root} = {n}.')
    add(16,'What is the smallest positive integer you multiply 1323 by to make a cube number?', [3,7,9,21],1,'1323 = 3³ × 7². Multiply by 7 to get 3³ × 7³ = 21³.')
    for statement,why in [
      ('The cube of any odd number is even.','An odd number multiplied by itself three times remains odd.'),
      ('There is no perfect cube that ends with 8.','2³ = 8 is a counterexample.'),
      ('The cube of a two-digit positive integer may be a three-digit number.','The smallest is 10³ = 1000, which already has four digits.'),
      ('The cube of a two-digit positive integer may have seven or more digits.','The largest is 99³ = 970299, which has six digits.'),
      ('Cube numbers always have an odd number of factors.','8 is a cube but has four positive factors: 1, 2, 4 and 8.')]:
        add(16,'True or false: '+statement,['True','False'],1,why)
    add(17,'Which of the following is the greatest?', ['67³ − 66³','43³ − 42³','67² − 66²','43² − 42²'],0,'The values are 13267, 5419, 133 and 85 respectively; 13267 is the greatest.')
    return bank
