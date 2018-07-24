## Parse and download FTP data 
## Dhemerson Conciani (dh.conciani@gmail.com)

library (RCurl)
library (curl)
library (tools)

## Define output path
setwd ("C:/espa_dwl/ftp")

## Define function
extract_pattern  = function (x) grep ("MAIACTBRF", x, value=TRUE)

## List files
URL <- getURL("ftp://maiac@dataportal.nccs.nasa.gov/DataRelease/SouthAmerica_2017/h02v01/2012/", verbose=TRUE, ftp.use.epsv=TRUE, dirlistonly = TRUE)

## List filenames using regular expression
filenames <- strsplit(URL, "\r*\n")

## Parse by pattern and map position
res <- lapply (filenames, extract_pattern)
list_length <- length(res[[1]])

## Mount download list
prefix = rep ("ftp://maiac@dataportal.nccs.nasa.gov/DataRelease/SouthAmerica_2017/h02v01/2012/", list_length)
link <- data.frame (prefix, res)
colnames(link)[2] <- "filename"
links <- with(link, paste0(prefix, filename))

## Download data
for (url in links) {
  download.file(url, destfile = basename(url))
}
