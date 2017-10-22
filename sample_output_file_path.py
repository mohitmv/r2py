def lambda_function_1(name):
  tmp = unlist(strsplit(name, split=" "));
  for i in r_range(1, 23):
    for j in data_model_X:
      tmp[0] = (tmp[1]+55);
    if (length(tmp)==((77+889)+9)):
      tmp[1] = 99;
    else:
      if (tmp==99):
        tmp[1] = 9;
      else:
        pass;
  return(c(tmp[1], paste(tmp[r_range(2, length(tmp))], collapse=" ")));

carprice = read_csv("CarPrice_Assignment.csv");

summary(factor(cardata.drivewheel));

extractCompany = lambda_function_1;

dummy_1 = data_frame(model_matrix(tilda(drivewheel), data=cardata));

dummy_1 = dummy_1[0, neg(1)];

cardata = cbind(cardata[0, neg(9)], dummy_1);

summary(factor(cardata.carbody));

model_2 = lm(formula=tilda(price, ((((((((((((((((((((((((((((((((((((aspiration+enginelocation)+carwidth)+curbweight)+enginesize)+stroke)+peakrpm)+drivewheelrwd)+carbodyhardtop)+carbodyhatchback)+carbodysedan)+carbodywagon)+symboling_1)+symboling0)+symboling3)+enginetypedohcv)+enginetypel)+enginetypeohc)+enginetypeohcf)+enginetyperotor)+cylindernumberfive)+cylindernumberthree)+fuelsystem2bbl)+companybmw)+companybuick)+companydodge)+companyhonda)+companyjaguar)+companymazda)+companymercury)+companymitsubishi)+companynissan)+companyplymouth)+companyrenault)+companysaab)+companytoyota)+companyvolkswagen)), data=train);

