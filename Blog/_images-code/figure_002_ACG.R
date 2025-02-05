
# setup -------------------------------------------------------------------
rm(list=ls())
graphics.off()
library(pacman)
pacman::p_load(ggplot2,
               rstudioapi,
               MASS,
               dplyr,
               plotly)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# Set seed for reproducibility
set.seed(123)

# Define scatter matrix (determines ACG spread)
Sigma <- matrix(c(2, 1, 1, 3), ncol=2)

# Sample from a Gaussian
samples <- mvrnorm(n = 1000, mu = c(0, 0), Sigma = Sigma)

# Normalize to lie on the unit circle (ACG transformation)
samples <- samples / sqrt(rowSums(samples^2))

# Convert to a data frame
df <- as.data.frame(samples)
colnames(df) <- c("x", "y")

# Create a beautiful 2D scatter + density plot
plot_now <- ggplot(df, aes(x, y)) +
  # Background gradient for aesthetics
  geom_tile(data = expand.grid(x = seq(-1, 1, length.out = 100), 
                               y = seq(-1, 1, length.out = 100)), 
            aes(x, y, fill = sqrt(x^2 + y^2)), alpha = 0.15) +
  scale_fill_gradient(low = "#F2F2F2", high = "#D8D8D8") + 
  
  # Points with transparency to highlight density
  geom_point(color = "#0072B2", alpha = 0.5, size = 1.2) +
  
  # Contour lines for density estimation
  geom_density_2d(color = "#D55E00", linewidth = 0.8, linetype = "solid") +
  
  # Circular reference line (unit circle)
  annotate("path", x = cos(seq(0, 2 * pi, length.out = 200)), 
           y = sin(seq(0, 2 * pi, length.out = 200)), color = "black", size = 0.7, linetype = "dashed") +
  
  # Theme adjustments for a clean, modern look
  coord_fixed() +
  theme_bw() +
  theme(panel.grid = element_blank(),
        panel.border = element_rect(linewidth=2),
        axis.text = element_blank(),
        axis.title = element_blank(),
        axis.ticks = element_blank(),
        legend.position = "none")
plot_path = file.path(dirname(getwd()),"images","figure_002_ACG.png")
ggsave(plot_path, plot=plot_now, width=4, height=4, dpi=300)
