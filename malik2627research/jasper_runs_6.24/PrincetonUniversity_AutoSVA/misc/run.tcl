clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/ft_fifo/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_mmu/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_ptw/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_tlb/sva /home/rk6650/VeriTriples/malik2627research/repos_6.24/PrincetonUniversity_AutoSVA/AUTOSVA_GEN.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/ft_fifo/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_mmu/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_ptw/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_tlb/sva /home/rk6650/VeriTriples/malik2627research/repos_6.24/PrincetonUniversity_AutoSVA/ft_ptw/sva/ptw_prop.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/ft_fifo/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_mmu/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_ptw/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_tlb/sva /home/rk6650/VeriTriples/malik2627research/repos_6.24/PrincetonUniversity_AutoSVA/ft_mmu/sva/mmu_prop.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/ft_fifo/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_mmu/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_ptw/sva -incdir /home/rk6650/VeriTriples/malik2627research/ft_tlb/sva /home/rk6650/VeriTriples/malik2627research/repos_6.24/PrincetonUniversity_AutoSVA/ft_tlb/sva/tlb_prop.sv }


            if {[catch {elaborate -top fifo} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/PrincetonUniversity_AutoSVA/misc/results.rpt
report_vacuity -out jasper_runs_6.24/PrincetonUniversity_AutoSVA/misc/vacuity.rpt
exit
