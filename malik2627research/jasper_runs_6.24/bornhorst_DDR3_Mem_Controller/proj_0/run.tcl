clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/hvl /home/rk6650/VeriTriples/malik2627research/repos_6.24/bornhorst_DDR3_Mem_Controller/hvl/ddr3_mem_sdram.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/hvl /home/rk6650/VeriTriples/malik2627research/repos_6.24/bornhorst_DDR3_Mem_Controller/hvl/lfsr.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/hvl /home/rk6650/VeriTriples/malik2627research/repos_6.24/bornhorst_DDR3_Mem_Controller/hvl/ddr3_mem_cpu.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/hvl /home/rk6650/VeriTriples/malik2627research/repos_6.24/bornhorst_DDR3_Mem_Controller/hvl/ddr3_mem_cont.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/hvl /home/rk6650/VeriTriples/malik2627research/repos_6.24/bornhorst_DDR3_Mem_Controller/hvl/ddr3_mem_cont.sv }


            if {[catch {elaborate -top ddr3_mem_cpu} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/bornhorst_DDR3_Mem_Controller/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/bornhorst_DDR3_Mem_Controller/proj_0/vacuity.rpt
exit
