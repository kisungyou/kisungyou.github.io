# example figures by their sizes
rm(list=ls())
library(ggplot2)
library(rstudioapi)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# some random histogram example -------------------------------------------
set.seed(1234)
df <- data.frame(
  sex=factor(rep(c("F", "M"), each=200)),
  weight=round(c(rnorm(200, mean=55, sd=5), rnorm(200, mean=65, sd=5)))
)
head(df)


# Basic histogram
p <- ggplot(df, aes(x=weight, color=sex)) +
  geom_histogram(fill="white")

# title
set1 <- p + ggtitle("width 2, height 1")
set2 <- p + ggtitle("width 3, height 2")
set3 <- p + ggtitle("width 4, height 3")

# save : names are units of "px" by "width x height"

ggsave("test_set1.png", set1, width=2, height=1)
ggsave("test_set2.png", set2, width=3, height=2)
ggsave("test_set3.png", set3, width=4, height=3)
