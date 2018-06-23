pragma solidity ^0.4.21;

// Timestamp Oracle
// Generated by ezo
//
// use at your own risk
//

contract TemperatureOracle {

    address public owner;
    uint public temp;
    uint public timestamp;

    event TempRequest(address sender);
    event FilledRequest(uint rtemp);

    function constructor() public {
        temp = 0;
        owner = msg.sender;
    }

    function request() public returns (string) {
        emit TempRequest(msg.sender);
        return "sent";
    }

    function fill(uint rtemp) public returns (uint){
        temp = rtemp;
        emit FilledRequest(rtemp);
        return temp;
    }


}