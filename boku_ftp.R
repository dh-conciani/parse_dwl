## Parse and download FTP data from BOKU servers
## An example using 4 independent lists
## For single orders, use only URL1/ filenames1/ Link1
## Dhemerson Conciani (dh.conciani@gmail.com)


library (RCurl)
library (curl)
library (tools)

## Define output path to alocate downloaded scenes
setwd ("~/Desktop/dwl_boku")

## Get list of scenes
URL1 <- getURL("ftp://141.244.38.19/9337cd38d5de72013bdbe2ffdf8d2868/filtered/", verbose=TRUE, ftp.use.epsv=TRUE, dirlistonly = TRUE)
URL2 <- getURL("ftp://141.244.38.19/e43b39b4a8774cfb2f804686c66a9396/filtered/", verbose=TRUE, ftp.use.epsv=TRUE, dirlistonly = TRUE)
URL3 <- getURL("ftp://141.244.38.19/6c618ba58a8ead4ad43d8e1f721757fa/filtered/", verbose=TRUE, ftp.use.epsv=TRUE, dirlistonly = TRUE)
URL4 <- getURL("ftp://141.244.38.19/fb5a3926e8501bd847bde3cadf9eda56/filtered/", verbose=TRUE, ftp.use.epsv=TRUE, dirlistonly = TRUE)

## List filenames using regular expression
filenames1 <- strsplit(URL1, "\r*\n")
filenames2 <- strsplit(URL2, "\r*\n")
filenames3 <- strsplit(URL3, "\r*\n")
filenames4 <- strsplit(URL4, "\r*\n")

## Map scene position into server
list_length <- length(filenames1[[1]])

## Mount download list
## Link1
prefix = rep ("ftp://141.244.38.19/9337cd38d5de72013bdbe2ffdf8d2868/filtered/", list_length)
link <- data.frame (prefix, filenames1)
colnames(link)[2] <- "filename"
links1 <- with(link, paste0(prefix, filename))

## Link2
prefix = rep ("ftp://141.244.38.19/e43b39b4a8774cfb2f804686c66a9396/filtered/", list_length)
link <- data.frame (prefix, filenames2)
colnames(link)[2] <- "filename"
links2 <- with(link, paste0(prefix, filename))

## Link3
prefix = rep ("ftp://141.244.38.19/6c618ba58a8ead4ad43d8e1f721757fa/filtered/", list_length)
link <- data.frame (prefix, filenames3)
colnames(link)[2] <- "filename"
links3 <- with(link, paste0(prefix, filename))

## Link4
prefix = rep ("ftp://141.244.38.19/fb5a3926e8501bd847bde3cadf9eda56/filtered/", list_length)
link <- data.frame (prefix, filenames4)
colnames(link)[2] <- "filename"
links4 <- with(link, paste0(prefix, filename))

## Aggregate all orders in a unique element
link = c(links1, links2, links3, links4)

## Clear memory
rm (filenames1, filenames2, filenames3, filenames4, list_length,
    URL1, URL2, URL3, URL4, prefix, links1, links2, links3, links4)

## Download data
for (url in link) {
  download.file(url, destfile = basename(url))
}
