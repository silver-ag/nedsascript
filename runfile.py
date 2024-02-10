from nedsascript import construct_nedsa
import sys

if __name__ == "__main__":
    with open(sys.argv[2]) as file:
      nedsa = construct_nedsa(file.read())
    if sys.argv[1] == 'run':
      print(nedsa.run())
    elif sys.argv[1] == 'decide':
      print(nedsa.decide(verbose = True))
    else:
      print('invalid arguments')
