#include "util.h"
#define DEBUG 0


std::string psiSchemeToString(PSIScheme psiScheme){
    switch(psiScheme){
        case Grr18: return "Grr18";
        case Rr17: return "Rr17";
        case Rr16: return "Rr16";
        case Dkt10: return "Dkt10";
        case Kkrt16: return "Kkrt16";
        case Drrt18: return "Drrt18";
        default: return "Scheme has no name";
    }
}

PSIScheme stringToPSIScheme(std::string schemeString){
    if(schemeString == "Grr18" || schemeString == "grr18" || schemeString == "GRR18")
        return Grr18;
    else if(schemeString == "Rr17" || schemeString == "rr17" || schemeString == "RR17")
        return Rr17;
    else if(schemeString == "Rr16" || schemeString == "rr16" || schemeString == "RR16")
        return Rr16;
    else if(schemeString == "Dkt10" || schemeString == "dkt10" || schemeString == "DKT10")
        return Dkt10;
    else if(schemeString == "Kkrt16" || schemeString == "kkrt16" || schemeString == "KKRT16")
        return Kkrt16;
    else if(schemeString ==  "Drrt18"|| schemeString == "drrt18" || schemeString == "DRRT18")
        return Drrt18;
    else
        return Grr18;
        
}

void _debug(std::string msg){
#if DEBUG
    ::std::cout << msg << ::std::endl;
#endif
}
