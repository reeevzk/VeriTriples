clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/SPI_protocol -incdir /home/rk6650/VeriTriples/malik2627research/UART_protocol /home/rk6650/VeriTriples/malik2627research/repos_6.24/SvrAdityaReddy_Inter_Device_Communication_Protocols/UART_protocol/uart.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/SPI_protocol -incdir /home/rk6650/VeriTriples/malik2627research/UART_protocol /home/rk6650/VeriTriples/malik2627research/repos_6.24/SvrAdityaReddy_Inter_Device_Communication_Protocols/UART_protocol/uart.sv }


            if {[catch {elaborate -top uart} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/SvrAdityaReddy_Inter_Device_Communication_Protocols/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/SvrAdityaReddy_Inter_Device_Communication_Protocols/proj_0/vacuity.rpt
exit
