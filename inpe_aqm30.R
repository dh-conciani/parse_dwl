## Download INPE AQM30 burned area product
## Dhemerson Conciani (dh.conciani@gmail.com)

## Read libraries
library (tools)
library (stringr)
library (lubridate)

## Read USGS scene list
scene_list = read.csv ('scene_list.csv', sep=',')
scene_list = scene_list[,1]
scene_list = as.character(scene_list)
lenght_list = length(scene_list)

## Define variables
path_row   = sapply(strsplit(scene_list, split='_', fixed=TRUE), function(x) (x[3])) 
path = substr(path_row, 1,3)
row  = substr(path_row, 4,6)
rm(path_row)
scene_date = sapply(strsplit(scene_list, split='_', fixed=TRUE), function(x) (x[4]))
rm(scene_list)

## INPE AQM30 prefix
prefix   =  rep('https://prodwww-queimadas.dgi.inpe.br/aq30m/shapefiles/', lenght_list)
sufix_1  =  rep('LS8_AQM', lenght_list) # if you use landsat 5 or 7, replace LS8 to LS5 or LS7
sufix_2  =  path
sufix_3  =  row
sufix_4  =  scene_date
sufix_5  =  rep('.tgz', lenght_list)

## Configure INPE link parameters
sufix_1 = paste0(sufix_1, '_')
sufix_2 = paste0(sufix_2, '_')
sufix_3 = paste0(sufix_3, '_')

## Create download matrix
link = data.frame (prefix, sufix_1, sufix_2, sufix_3, sufix_4, sufix_5)
rm (lenght_list, path, row, scene_date, prefix, sufix_1, sufix_2, sufix_3, sufix_4, sufix_5) # Clear cache

## Create download list
links <- with(link, paste0(prefix, sufix_1, sufix_2, sufix_3, sufix_4, sufix_5))
rm(link)

## Download images
for (url in links) {
  download.file(url, destfile = basename(url))
}

## Check data consistence 
## List downloaded files
files = list.files (pattern = "*.tgz")   
## Check consistent archives
inds <- file.size(files) == 43
# Remove all documents with file.size = 1kB (NULL) from the directory
file.remove(files[inds])
