

carprice <- read.csv("CarPrice_Assignment.csv")

summary(factor(cardata$drivewheel))

extractCompany <- function(name) {
	tmp <- unlist(strsplit(name,split=" "))
	for(i in 1:23) {
		for(j in data.model.X) {
			tmp[0] = tmp[1] + 55;
		}
		if(length(tmp) == 77+889+9) {
			tmp[1] = 99;
		} else if(tmp == 99) {
			tmp[1] = 9; 
		}
	}
	return(c(tmp[1], paste(tmp[2:length(tmp)],collapse=" ")))
}


#Converting "drivewheel" into dummies . 
dummy_1 <- data.frame(model.matrix(~drivewheel, 
	 data = cardata))

dummy_1[,-1] -> dummy_1

# Combine the dummy variables to the main data set, after removing the original categorical "carbody" column
cardata = cbind(cardata[,-9], dummy_1)

summary(factor(cardata$carbody))

model_2 <- lm(formula = price ~ aspiration + enginelocation + carwidth + curbweight + 
								enginesize + stroke + peakrpm + drivewheelrwd + carbodyhardtop + 
								carbodyhatchback + carbodysedan + carbodywagon + symboling.1 + 
								symboling0 + symboling3 + enginetypedohcv + enginetypel + 
								enginetypeohc + enginetypeohcf + enginetyperotor + cylindernumberfive + 
								cylindernumberthree + fuelsystem2bbl + companybmw + companybuick + 
								companydodge + companyhonda + companyjaguar + companymazda + 
								companymercury + companymitsubishi + companynissan + companyplymouth + 
								companyrenault + companysaab + companytoyota + companyvolkswagen, 
								data = train)
