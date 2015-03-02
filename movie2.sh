
awk '{print $0".jpg"}' $1/framelist.txt >framelist.txt
sed -i '' -e"s/^/$1\//" framelist.txt
mencoder mf://@framelist.txt -mf w=1024:h=1024:fps=20:type=jpg -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell:vbitrate=2500 -oac copy -o $1.avi
