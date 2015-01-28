ls $1/*.jpg | sort -n -t/ -k2 >framelist.txt
mencoder mf://@framelist.txt -mf w=640:h=640:fps=20:type=jpg -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell:vbitrate=2500 -oac copy -o $1.avi
