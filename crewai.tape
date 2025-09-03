# Where should we write the GIF?
Output ./imgs/demo.gif

# Set up a 1800x1200 terminal with 16px font.
Set Width 1800
Set Height 1200
Set FontSize 16

# Use bash as the shell to avoid Zsh prompt issues
Set Shell bash

Type "crewai run"
Enter

# Wait for the specific output string to appear using a regular expression
Sleep 48s

Type "ls -l ./outputs"
Enter
Sleep 1s

Type "glow ./outputs/kubernetes-v1.33-new_features_report.md"
Enter
Sleep 3s