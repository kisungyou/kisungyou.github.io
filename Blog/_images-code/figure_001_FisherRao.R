rm(list=ls())
graphics.off()
library(ggplot2)
library(rstudioapi)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Function to compute the Fisher-Rao geodesic path between two Beta distributions
beta_geodesic <- function(alpha1, beta1, alpha2, beta2, t_seq) {
  params <- lapply(t_seq, function(t) {
    a_t <- (1 - t) * alpha1 + t * alpha2
    b_t <- (1 - t) * beta1 + t * beta2
    if (a_t > 0 & b_t > 0) {
      return(c(a_t, b_t))  # Return as a numeric vector instead of a list
    } else {
      return(NULL)
    }
  })
  params <- Filter(Negate(is.null), params)  # Remove invalid parameter pairs
  return(params)
}

# Set parameters for two Beta distributions
alpha1 <- 2; beta1 <- 5
alpha2 <- 5; beta2 <- 2

# Define a sequence of interpolation points (t in [0,1])
t_seq <- seq(0, 1, length.out = 11)

# Generate the geodesic path
params <- beta_geodesic(alpha1, beta1, alpha2, beta2, t_seq)

# Generate densities for visualization
x_vals <- seq(0, 1, length.out = 100)
densities <- do.call(rbind, lapply(seq_along(params), function(i) {
  a_t <- as.numeric(params[[i]][1])  # Explicitly convert to numeric
  b_t <- as.numeric(params[[i]][2])  # Explicitly convert to numeric
  data.frame(x = x_vals, 
             density = dbeta(x_vals, a_t, b_t),
             t = i)  # Use index to avoid mismatches
}))

# Plot
plot_now = ggplot(densities, aes(x, density, color = factor(t))) +
  geom_line(size = 1) +
  scale_color_viridis_d(name = "Interpolation") +
  theme_bw() + 
  theme(legend.position = "none") + 
  theme(panel.grid = element_blank()) + 
  theme(axis.text = element_blank()) + 
  theme(axis.title = element_blank()) + 
  theme(panel.border = element_rect(linewidth=2))
plot_path = file.path(dirname(getwd()),"images","figure_001_FisherRao.png")
ggsave(plot_path, plot=plot_now, width=6, height=4, dpi=300)
