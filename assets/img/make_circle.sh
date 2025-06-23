
#!/bin/bash

input="$1"
output="$2"
bgcolor=${3:-"#ccf2ff"}  # 默认为浅蓝色

# 先获取图片宽高
read w h <<< $(magick identify -format "%w %h" "$input")

# 取最大边，生成正方形画布
size=$(( w > h ? w : h ))

magick -size ${size}x${size} canvas:"$bgcolor" \
       \( "$input" -gravity center -extent ${size}x${size} \) \
       -compose over -composite \
       \( -size ${size}x${size} xc:none -fill white -draw "circle $((size/2)),$((size/2)) $((size/2)),1" \) \
       -compose DstIn -composite \
       "$output"
