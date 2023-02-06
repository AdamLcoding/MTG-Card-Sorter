import os

alphabeticalSort = True
colorSpecific = True
setSpecific = True

numCardsSaved = len(os.listdir('src/Text_Output_Storage'))
inputCardOnePath = f'src/Text_Output_Storgae/card{numCardsSaved-1}'
inputCardTwoPath = f'src/Text_Output_Storgae/card{numCardsSaved-2}'

sortingPiles = []